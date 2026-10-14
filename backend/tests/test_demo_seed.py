import random
from datetime import datetime

import pytest
from sqlalchemy import func, select

from app import demo_seed
from app.models import LearningRole, Module, Organisation, Tier, User, UserModuleProgress


def test_refuses_to_run_against_a_real_database(monkeypatch):
    monkeypatch.setattr(demo_seed.settings, "database_url", "postgresql+asyncpg://sedna:sedna@db:5432/sedna")
    with pytest.raises(SystemExit):
        demo_seed._demo_url()


def test_reads_the_catalogue_from_the_matching_real_database(monkeypatch):
    monkeypatch.delenv("SOURCE_DATABASE_URL", raising=False)
    assert demo_seed._source_url("postgresql+asyncpg://u:p@db:5432/sedna_demo") == "postgresql+asyncpg://u:p@db:5432/sedna"


async def test_generates_fictional_companies_and_activity(db_session):
    role = LearningRole(name="Shipping from Scratch", audience="internal", products=["vms"])
    db_session.add(role)
    await db_session.flush()
    tier = Tier(role_id=role.id, label="The Industry", name="The Industry", cert_name="The Industry")
    db_session.add(tier)
    await db_session.flush()
    db_session.add_all([
        Module(tier_id=tier.id, title=f"Lesson {i}", module_type="a", duration_mins=6, sort_order=i) for i in range(5)
    ])
    await db_session.commit()

    await demo_seed._generate(db_session, random.Random("test"), datetime.utcnow())

    kinds = dict((await db_session.execute(select(Organisation.name, Organisation.kind))).all())
    assert kinds["Sedna"] == "sedna" and list(kinds.values()).count("customer") == 4
    assert await db_session.scalar(select(func.count()).select_from(User)) == 53  # 52 learners + demo admin
    assert await db_session.scalar(select(func.count()).select_from(UserModuleProgress)) > 0
    # The demo opens this path to customers
    assert (await db_session.get(LearningRole, role.id)).audience == "customer"
