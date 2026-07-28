from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from sqlalchemy import select

from app.models.user import User
from tests.conftest import auth_headers


async def _invite(client, admin, email="newbie@example.com"):
    with patch("app.routers.team.send_invite_email", new=AsyncMock()) as mock_email:
        resp = await client.post("/team/invite", headers=auth_headers(admin), json={
            "email": email, "name": "New Bie", "role": "Learner",
        })
    assert resp.status_code == 200
    return mock_email.call_args.args[3]  # invite_token positional arg


async def test_get_invite_returns_info_for_valid_token(client, admin):
    token = await _invite(client, admin)
    resp = await client.get(f"/auth/invite/{token}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "newbie@example.com"
    assert body["name"] == "New Bie"


async def test_get_invite_404s_for_unknown_token(client, admin):
    resp = await client.get("/auth/invite/not-a-real-token")
    assert resp.status_code == 404


async def test_accept_invite_sets_password_and_activates(client, admin):
    token = await _invite(client, admin)

    resp = await client.post("/auth/accept-invite", json={"token": token, "password": "supersecret123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

    result = await client.get("/team", headers=auth_headers(admin))
    newbie = next(u for u in result.json() if u["email"] == "newbie@example.com")
    assert newbie["status"] == "active"


async def test_accept_invite_token_cannot_be_reused(client, admin):
    token = await _invite(client, admin)
    await client.post("/auth/accept-invite", json={"token": token, "password": "supersecret123"})

    resp = await client.post("/auth/accept-invite", json={"token": token, "password": "anotherpassword"})
    assert resp.status_code == 404


async def test_accept_invite_rejects_expired_token(client, admin, db_session):
    token = await _invite(client, admin)
    result = await db_session.execute(select(User).where(User.invite_token == token))
    invite = result.scalar_one()
    invite.invite_token_expires_at = datetime.utcnow() - timedelta(days=1)
    await db_session.commit()

    resp = await client.post("/auth/accept-invite", json={"token": token, "password": "supersecret123"})
    assert resp.status_code == 400


async def test_accept_invite_rejects_short_password(client, admin):
    token = await _invite(client, admin)
    resp = await client.post("/auth/accept-invite", json={"token": token, "password": "short"})
    assert resp.status_code == 422


async def test_accepted_invite_can_then_log_in_normally(client, admin):
    token = await _invite(client, admin)
    await client.post("/auth/accept-invite", json={"token": token, "password": "supersecret123"})

    resp = await client.post("/auth/login", json={"email": "newbie@example.com", "password": "supersecret123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
