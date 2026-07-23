from datetime import date, timedelta

from sqlalchemy import select

from app.models.user import User
from app.services.auth import hash_password
from tests.conftest import auth_headers


async def _make_user(db_session, org, email, name="Someone", **kwargs):
    u = User(
        org_id=org.id, email=email, name=name, initial=name[0].upper(),
        role="Member", status="active", password_hash=hash_password("password123"),
        is_admin=False, **kwargs,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


# ── Departments ─────────────────────────────────────────────────────────
async def test_non_admin_cannot_create_department(client, user):
    resp = await client.post("/admin/departments", headers=auth_headers(user), json={"name": "Support"})
    assert resp.status_code == 403


async def test_admin_department_crud(client, admin):
    headers = auth_headers(admin)
    r = await client.post("/admin/departments", headers=headers, json={"name": "Support"})
    assert r.status_code == 200
    dept = r.json()
    assert dept["name"] == "Support"
    assert dept["member_count"] == 0

    r = await client.patch(f"/admin/departments/{dept['id']}", headers=headers, json={"name": "Customer Support"})
    assert r.status_code == 200
    assert r.json()["name"] == "Customer Support"

    r = await client.delete(f"/admin/departments/{dept['id']}", headers=headers)
    assert r.status_code == 200


async def test_delete_department_with_members_is_rejected(client, admin, db_session, org):
    headers = auth_headers(admin)
    r = await client.post("/admin/departments", headers=headers, json={"name": "Support"})
    dept_id = r.json()["id"]

    member = await _make_user(db_session, org, "member@example.com")
    await client.patch(f"/team/{member.id}", headers=headers, json={"department_id": dept_id})

    r = await client.delete(f"/admin/departments/{dept_id}", headers=headers)
    assert r.status_code == 400


# ── Manager scoping ─────────────────────────────────────────────────────
async def test_plain_learner_cannot_list_or_create_assignments(client, user, tier_with_modules):
    r = await client.get("/assignments", headers=auth_headers(user))
    assert r.status_code == 403

    r = await client.post("/assignments", headers=auth_headers(user), json={
        "user_ids": [user.id], "tier_id": tier_with_modules.id,
    })
    assert r.status_code == 403


async def test_department_manager_can_assign_and_view_their_department_only(
    client, admin, db_session, org, tier_with_modules
):
    headers = auth_headers(admin)
    manager = await _make_user(db_session, org, "manager@example.com", name="Manny Manager")
    in_dept = await _make_user(db_session, org, "indept@example.com", name="In Dept")
    out_dept = await _make_user(db_session, org, "outdept@example.com", name="Out Dept")

    r = await client.post("/admin/departments", headers=headers, json={"name": "Sales", "manager_user_id": manager.id})
    dept_id = r.json()["id"]
    await client.patch(f"/team/{in_dept.id}", headers=headers, json={"department_id": dept_id})

    manager_headers = auth_headers(manager)

    # Manager can assign to their own department member
    r = await client.post("/assignments", headers=manager_headers, json={
        "user_ids": [in_dept.id], "tier_id": tier_with_modules.id, "mandatory": True,
    })
    assert r.status_code == 200

    # Manager cannot assign to someone outside their department
    r = await client.post("/assignments", headers=manager_headers, json={
        "user_ids": [out_dept.id], "tier_id": tier_with_modules.id,
    })
    assert r.status_code == 403

    # Manager's compliance view only shows their department
    r = await client.get("/assignments", headers=manager_headers)
    assert r.status_code == 200
    seen_users = {a["user_id"] for a in r.json()}
    assert seen_users == {in_dept.id}


# ── Assignment status computation ───────────────────────────────────────
async def test_assignment_status_transitions_with_progress(client, admin, user, tier_with_modules):
    headers = auth_headers(admin)
    r = await client.post("/assignments", headers=headers, json={
        "user_ids": [user.id], "tier_id": tier_with_modules.id, "mandatory": True,
    })
    assert r.status_code == 200
    assert r.json()[0]["status"] == "not_started"

    module_id = tier_with_modules.modules[0].id
    await client.post(f"/progress/modules/{module_id}/complete", headers=auth_headers(user))

    r = await client.get("/assignments/me", headers=auth_headers(user))
    a = r.json()[0]
    assert a["status"] == "in_progress"
    assert a["pct_complete"] == 50.0

    module_id2 = tier_with_modules.modules[1].id
    await client.post(f"/progress/modules/{module_id2}/complete", headers=auth_headers(user))

    r = await client.get("/assignments/me", headers=auth_headers(user))
    a = r.json()[0]
    assert a["status"] == "complete"
    assert a["pct_complete"] == 100.0


async def test_overdue_assignment_status(client, admin, user, tier_with_modules):
    headers = auth_headers(admin)
    past_due = (date.today() - timedelta(days=3)).isoformat()
    r = await client.post("/assignments", headers=headers, json={
        "user_ids": [user.id], "tier_id": tier_with_modules.id, "due_date": past_due, "mandatory": True,
    })
    assert r.json()[0]["status"] == "overdue"


async def test_bulk_assign_to_department(client, admin, db_session, org, tier_with_modules):
    headers = auth_headers(admin)
    r = await client.post("/admin/departments", headers=headers, json={"name": "Sales"})
    dept_id = r.json()["id"]

    m1 = await _make_user(db_session, org, "m1@example.com")
    m2 = await _make_user(db_session, org, "m2@example.com")
    await client.patch(f"/team/{m1.id}", headers=headers, json={"department_id": dept_id})
    await client.patch(f"/team/{m2.id}", headers=headers, json={"department_id": dept_id})

    r = await client.post("/assignments", headers=headers, json={
        "user_ids": [], "department_id": dept_id, "tier_id": tier_with_modules.id, "mandatory": True,
    })
    assert r.status_code == 200
    assert {a["user_id"] for a in r.json()} == {m1.id, m2.id}


# ── Due-date reminders ───────────────────────────────────────────────────
async def test_reminder_dedup_only_sends_once_per_bucket(client, admin, user, tier_with_modules):
    headers = auth_headers(admin)
    past_due = (date.today() - timedelta(days=1)).isoformat()
    await client.post("/assignments", headers=headers, json={
        "user_ids": [user.id], "tier_id": tier_with_modules.id, "due_date": past_due, "mandatory": True,
    })

    r = await client.post("/admin/assignments/send-reminders", headers=headers)
    assert r.json()["reminders_sent"] == 1

    r = await client.post("/admin/assignments/send-reminders", headers=headers)
    assert r.json()["reminders_sent"] == 0


async def test_reminder_not_sent_for_completed_assignment(client, admin, user, tier_with_modules):
    headers = auth_headers(admin)
    past_due = (date.today() - timedelta(days=1)).isoformat()
    await client.post("/assignments", headers=headers, json={
        "user_ids": [user.id], "tier_id": tier_with_modules.id, "due_date": past_due, "mandatory": True,
    })
    for m in tier_with_modules.modules:
        await client.post(f"/progress/modules/{m.id}/complete", headers=auth_headers(user))

    r = await client.post("/admin/assignments/send-reminders", headers=headers)
    assert r.json()["reminders_sent"] == 0
