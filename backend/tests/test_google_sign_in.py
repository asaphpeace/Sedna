"""Google sign-in: sedna.com staff get in, customers only when invited and
their domain is allowed, and tokens must be signed by Google for our app."""
import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, jwt

from app.config import settings
from app.models import Organisation, User

CLIENT_ID = "test-client.apps.googleusercontent.com"
_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_pem = _key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
_public = jwk.construct(_key.public_key().public_bytes(
    serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo), "RS256").to_dict()
_public.update(kid="test-key", use="sig", alg="RS256")


def google_token(email, hd=None, verified=True, aud=CLIENT_ID, iss="https://accounts.google.com", name="Test Person"):
    claims = {"iss": iss, "aud": aud, "sub": "123", "email": email, "email_verified": verified,
              "name": name, "iat": int(time.time()), "exp": int(time.time()) + 600}
    if hd:
        claims["hd"] = hd
    return jwt.encode(claims, _pem, algorithm="RS256", headers={"kid": "test-key"})


@pytest.fixture(autouse=True)
def google_on(monkeypatch):
    from app.routers.auth import limiter
    limiter.reset()  # sign-in is rate-limited; these tests sign in many times
    async def keys():
        return {"keys": [_public]}
    monkeypatch.setattr("app.services.google_sign_in._google_keys", keys)
    monkeypatch.setattr(settings, "google_client_id", CLIENT_ID)
    monkeypatch.setattr(settings, "google_staff_domains", "sedna.com")
    monkeypatch.setattr(settings, "google_customer_domains", "")


async def sign_in(client, token):
    return await client.post("/auth/google", json={"credential": token})


async def test_config_exposes_client_id(client):
    assert (await client.get("/auth/config")).json() == {"google_client_id": CLIENT_ID}


async def test_new_sedna_person_joins_as_staff_learner(client, org, db_session):
    resp = await sign_in(client, google_token("New.Person@sedna.com", hd="sedna.com", name="New Person"))
    assert resp.status_code == 200
    me = (await client.get("/auth/me", headers={"Authorization": f"Bearer {resp.json()['access_token']}"})).json()
    assert me["email"] == "new.person@sedna.com" and me["name"] == "New Person"
    assert me["is_sedna_staff"] is True and me["is_admin"] is False


async def test_existing_account_signs_in(client, user):
    domain = user.email.rpartition("@")[2]
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(settings, "google_staff_domains", domain)
        resp = await sign_in(client, google_token(user.email, hd=domain))
    assert resp.status_code == 200


@pytest.mark.parametrize("email,hd,verified", [
    ("someone@gmail.com", None, True),          # not an allowed domain
    ("someone@sedna.com", None, True),          # personal Google account on a work address
    ("someone@sedna.com", "other.com", True),   # hosted domain doesn't match
    ("someone@sedna.com", "sedna.com", False),  # email not verified
])
async def test_refused(client, org, email, hd, verified):
    assert (await sign_in(client, google_token(email, hd=hd, verified=verified))).status_code == 403


async def test_token_must_be_for_this_app_and_from_google(client, org):
    assert (await sign_in(client, google_token("a@sedna.com", hd="sedna.com", aud="someone-else"))).status_code == 401
    assert (await sign_in(client, google_token("a@sedna.com", hd="sedna.com", iss="https://evil.example"))).status_code == 401
    assert (await sign_in(client, "not-a-token")).status_code == 401


async def test_customers_are_invite_only(client, db_session, monkeypatch):
    acme = Organisation(name="Acme Bulk", slug="acme", kind="customer")
    db_session.add(acme)
    await db_session.flush()
    db_session.add(User(org_id=acme.id, email="ada@acme.example", name="Ada", initial="A",
                        status="invited", invite_token="tok-123"))
    await db_session.commit()

    # Domain not switched on yet: refused even though invited
    assert (await sign_in(client, google_token("ada@acme.example", hd="acme.example"))).status_code == 403

    monkeypatch.setattr(settings, "google_customer_domains", "acme.example")
    assert (await sign_in(client, google_token("ada@acme.example", hd="acme.example"))).status_code == 200
    ada = (await db_session.execute(
        User.__table__.select().where(User.email == "ada@acme.example"))).one()
    assert ada.status == "active" and ada.invite_token is None
    # Not invited: no self-registration for customers
    assert (await sign_in(client, google_token("bob@acme.example", hd="acme.example"))).status_code == 403


async def test_removed_people_stay_out(client, user, db_session):
    domain = user.email.rpartition("@")[2]
    row = await db_session.get(User, user.id)
    row.status = "removed"
    await db_session.commit()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(settings, "google_staff_domains", domain)
        assert (await sign_in(client, google_token(user.email, hd=domain))).status_code == 403


async def test_off_without_client_id(client, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "")
    assert (await client.get("/auth/config")).json() == {"google_client_id": None}
    assert (await sign_in(client, google_token("a@sedna.com", hd="sedna.com"))).status_code == 404
