from datetime import datetime, timedelta

import pytest_asyncio
from sqlalchemy import select

from app.models import Certificate, LearningTime, Organisation, User, UserModuleProgress
from tests.conftest import auth_headers


@pytest_asyncio.fixture
async def sedna_admin(db_session, org):
    org.kind = "sedna"
    u = User(org_id=org.id, email="nassia@example.com", name="Nassia", initial="N",
             status="active", is_admin=True)
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def customer(db_session):
    o = Organisation(name="Acme Bulk", slug="acme-bulk", kind="customer")
    db_session.add(o)
    await db_session.flush()
    u = User(org_id=o.id, email="cara@acme.example", name="Cara Customer", initial="C", status="active")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


def _done(user, module, days_ago, took_days=0):
    now = datetime.utcnow()
    return UserModuleProgress(
        user_id=user.id, module_id=module.id, state="done", pct_complete=100,
        started_at=now - timedelta(days=days_ago + took_days), completed_at=now - timedelta(days=days_ago),
    )


async def test_only_sedna_admins_can_see_it(client, admin, sedna_admin, customer, db_session):
    # A customer company's own admin is refused
    customer.is_admin = True
    await db_session.commit()
    assert (await client.get("/analytics/impact", headers=auth_headers(customer))).status_code == 403
    assert (await client.get("/analytics/impact", headers=auth_headers(sedna_admin))).status_code == 200


async def test_reach_counts_lessons_people_and_time(client, db_session, sedna_admin, user, customer, tier_with_modules):
    m1, m2 = tier_with_modules.modules
    db_session.add_all([
        _done(user, m1, days_ago=0),        # staff, this month
        _done(customer, m1, days_ago=0),    # customer, this month
        _done(customer, m2, days_ago=0),
        LearningTime(user_id=customer.id, module_id=m1.id, day=datetime.utcnow().date(), seconds=600),
        Certificate(user_id=customer.id, tier_id=tier_with_modules.id, credential_number="SA-1"),
    ])
    await db_session.commit()

    data = (await client.get("/analytics/impact?period=month", headers=auth_headers(sedna_admin))).json()
    h = data["headline"]
    assert h["lessons"]["value"] == 3
    assert h["people"]["value"] == 2
    assert h["certificates"]["value"] == 1
    assert h["tracked_minutes"]["value"] == 10
    assert h["estimated_minutes"]["value"] == 15  # three 5-minute lessons

    customers_only = (await client.get(
        "/analytics/impact?period=month&audience=customer", headers=auth_headers(sedna_admin)
    )).json()
    assert customers_only["headline"]["lessons"]["value"] == 2
    assert [c["name"] for c in customers_only["companies"]] == ["Acme Bulk"]


async def test_health_finds_finishers_and_drop_off(client, db_session, sedna_admin, user, customer, tier_with_modules):
    m1, m2 = tier_with_modules.modules
    db_session.add_all([
        _done(customer, m1, days_ago=1, took_days=2),
        _done(customer, m2, days_ago=1),
        _done(user, m1, days_ago=30),  # stopped before Module Two, idle for 30 days
    ])
    await db_session.commit()

    data = (await client.get("/analytics/impact?period=12m", headers=auth_headers(sedna_admin))).json()
    path = data["paths"][0]
    assert (path["started"], path["finished"], path["completion_rate"]) == (2, 1, 50)
    assert path["dropoff"]["title"] == "Module Two"
    assert [r["name"] for r in data["attention"]["idle_learners"]] == ["Lauren Learner"]


async def test_time_is_recorded_per_day_and_capped(client, db_session, user, tier_with_modules):
    m1 = tier_with_modules.modules[0]
    for _ in range(3):
        r = await client.post(f"/progress/modules/{m1.id}/time", json={"seconds": 30}, headers=auth_headers(user))
        assert r.status_code == 200
    too_much = await client.post(f"/progress/modules/{m1.id}/time", json={"seconds": 3600}, headers=auth_headers(user))
    assert too_much.status_code == 422

    rows = (await db_session.execute(select(LearningTime))).scalars().all()
    assert [(r.seconds) for r in rows] == [90]
