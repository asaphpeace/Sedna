"""Customer companies are kept apart; only Sedna admins manage the catalogue."""
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest_asyncio
from sqlalchemy import select

from app.models import (
    Certificate, LearningRole, Module, ModuleComment, Organisation, Tier, User, UserModuleProgress,
)
from tests.conftest import auth_headers


async def _company(db, name):
    o = Organisation(name=name, slug=name.lower().replace(" ", "-"), kind="customer")
    db.add(o)
    await db.flush()
    return o


async def _person(db, org, email, admin=False):
    u = User(org_id=org.id, email=email, name=email.split("@")[0].title(), initial="X",
             status="active", is_admin=admin)
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


@pytest_asyncio.fixture
async def acme(db_session):
    org = await _company(db_session, "Acme Bulk")
    return {
        "org": org,
        "admin": await _person(db_session, org, "ada@acme.example", admin=True),
        "learner": await _person(db_session, org, "lee@acme.example"),
    }


@pytest_asyncio.fixture
async def other(db_session):
    org = await _company(db_session, "Other Tankers")
    return {"org": org, "learner": await _person(db_session, org, "oz@other.example")}


@pytest_asyncio.fixture
async def staff_path(db_session):
    role = LearningRole(name="VMS Support", audience="internal", products=["vms"])
    db_session.add(role)
    await db_session.flush()
    tier = Tier(role_id=role.id, label="Foundation", name="Foundation", cert_name="VMS Support Foundation")
    db_session.add(tier)
    await db_session.flush()
    m = Module(tier_id=tier.id, title="Internal lesson", module_type="a", sort_order=0)
    db_session.add(m)
    await db_session.commit()
    return role, m


# ── The catalogue ────────────────────────────────────────

async def test_customer_admin_cannot_change_the_catalogue(client, acme, tier_with_modules):
    h = auth_headers(acme["admin"])
    m = tier_with_modules.modules[0]
    assert (await client.patch(f"/admin/modules/{m.id}", json={"title": "Hacked"}, headers=h)).status_code == 403
    assert (await client.delete(f"/admin/modules/{m.id}", headers=h)).status_code == 403
    assert (await client.post("/admin/paths", json={"name": "Mine"}, headers=h)).status_code == 403


async def test_customers_only_see_customer_paths(client, acme, admin, staff_path, tier_with_modules):
    role, internal_lesson = staff_path
    h = auth_headers(acme["learner"])

    names = [p["name"] for p in (await client.get("/paths", headers=h)).json()]
    assert "VMS Support" not in names and "Test Path" in names
    assert (await client.get(f"/paths/{role.id}", headers=h)).status_code == 404
    assert (await client.get(f"/modules/{internal_lesson.id}", headers=h)).status_code == 404
    assert internal_lesson.id not in [m["id"] for m in (await client.get("/modules", headers=h)).json()]
    assert (await client.post(f"/progress/modules/{internal_lesson.id}/complete", headers=h)).status_code == 404
    assert (await client.get(f"/quizzes/module/{internal_lesson.id}", headers=h)).status_code == 404

    # Sedna staff still see it
    staff_names = [p["name"] for p in (await client.get("/paths", headers=auth_headers(admin))).json()]
    assert "VMS Support" in staff_names


async def test_comments_are_staff_only(client, acme, admin, tier_with_modules):
    m = tier_with_modules.modules[0]
    assert (await client.get(f"/social/modules/{m.id}/comments", headers=auth_headers(acme["learner"]))).status_code == 403
    assert (await client.get(f"/social/modules/{m.id}/comments", headers=auth_headers(admin))).status_code == 200


# ── People ───────────────────────────────────────────────

async def test_customer_admin_sees_only_their_company(client, acme, other):
    h = auth_headers(acme["admin"])
    emails = [u["email"] for u in (await client.get("/team", headers=h)).json()]
    assert set(emails) == {"ada@acme.example", "lee@acme.example"}
    assert (await client.get("/admin/companies", headers=h)).status_code == 403
    assert (await client.get("/analytics/impact", headers=h)).status_code == 403
    # Can't remove someone in another company — looks like they don't exist
    assert (await client.delete(f"/admin/users/{other['learner'].id}", headers=h)).status_code == 404


async def test_sedna_admin_sets_up_a_company_and_invites_its_admin(client, admin):
    h = auth_headers(admin)
    company = (await client.post("/admin/companies", json={"name": "Kestrel Line"}, headers=h)).json()
    assert company["kind"] == "customer"
    assert (await client.post("/admin/companies", json={"name": "kestrel line"}, headers=h)).status_code == 409

    with patch("app.services.accounts.send_invite_email", new=AsyncMock()) as email:
        r = await client.post(f"/admin/companies/{company['id']}/invite", headers=h,
                              json={"email": "kim@kestrel.example", "name": "Kim", "is_admin": True})
    assert r.status_code == 200 and r.json()["is_admin"] is True and r.json()["org_id"] == company["id"]
    email.assert_awaited_once()

    listed = {c["name"]: c for c in (await client.get("/admin/companies", headers=h)).json()}
    assert (listed["Kestrel Line"]["people"], listed["Kestrel Line"]["admins"]) == (1, 1)


# ── Removal on request (GDPR) ────────────────────────────

async def test_removal_anonymises_but_keeps_completions(client, db_session, acme, admin, tier_with_modules):
    lee = acme["learner"]
    lee_id, token, ada, nassia = lee.id, auth_headers(lee), auth_headers(acme["admin"]), auth_headers(admin)
    m = tier_with_modules.modules[0]
    db_session.add_all([
        UserModuleProgress(user_id=lee.id, module_id=m.id, state="done", pct_complete=100,
                           started_at=datetime.utcnow(), completed_at=datetime.utcnow()),
        Certificate(user_id=lee.id, tier_id=tier_with_modules.id, credential_number="SA-9"),
        ModuleComment(module_id=m.id, user_id=lee.id, body="My question"),
    ])
    await db_session.commit()

    # Their own company's admin can remove them
    assert (await client.delete(f"/admin/users/{lee_id}", headers=ada)).status_code == 204

    db_session.expire_all()
    gone = await db_session.get(User, lee_id)
    assert (gone.name, gone.status, gone.password_hash) == ("Removed learner", "removed", None)
    assert "lee" not in gone.email
    assert (await db_session.execute(select(ModuleComment).where(ModuleComment.user_id == lee_id))).first() is None
    assert (await db_session.execute(select(UserModuleProgress).where(UserModuleProgress.user_id == lee_id))).first()

    # Their old session stops working, and they drop out of team lists
    assert (await client.get("/auth/me", headers=token)).status_code == 401
    emails = [u["email"] for u in (await client.get("/team", headers=ada)).json()]
    assert emails == ["ada@acme.example"]

    # Their lesson still counts for Nassia
    data = (await client.get("/analytics/impact?period=12m", headers=nassia)).json()
    assert data["headline"]["lessons"]["value"] == 1
    acme_row = next(c for c in data["companies"] if c["name"] == "Acme Bulk")
    assert acme_row["users"] == 1  # only Ada is still a person here


async def test_status_cannot_be_set_to_removed_directly(client, acme):
    r = await client.patch(f"/team/{acme['learner'].id}", json={"status": "removed"},
                           headers=auth_headers(acme["admin"]))
    assert r.status_code == 400
