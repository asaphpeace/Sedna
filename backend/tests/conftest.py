import os
import random
import string

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy.pool import NullPool

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://sedna:sedna@localhost:5440/sedna_test",
)
os.environ.setdefault("ENV", "development")

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import *  # noqa: E402,F401,F403 — register all models with Base
from app.models.content import LearningRole, Tier, Module  # noqa: E402
from app.models.user import Organisation, User  # noqa: E402
from app.services.auth import create_access_token, hash_password  # noqa: E402
from app.schemas.auth import TokenData  # noqa: E402

TEST_DB_URL = os.environ["DATABASE_URL"]
engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables():
    """Truncate all tables before every test for isolation."""
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def _rand_slug():
    return "org-" + "".join(random.choices(string.ascii_lowercase, k=8))


@pytest_asyncio.fixture
async def org(db_session):
    o = Organisation(name="Test Org", slug=_rand_slug())
    db_session.add(o)
    await db_session.commit()
    await db_session.refresh(o)
    return o


@pytest_asyncio.fixture
async def user(db_session, org):
    u = User(
        org_id=org.id,
        email="learner@example.com",
        name="Lauren Learner",
        initial="L",
        role="Support Engineer",
        status="active",
        password_hash=hash_password("password123"),
        is_admin=False,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def admin(db_session, org):
    u = User(
        org_id=org.id,
        email="admin@example.com",
        name="Adam Admin",
        initial="A",
        role="Admin",
        status="active",
        password_hash=hash_password("password123"),
        is_admin=True,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


def auth_headers(u: User) -> dict:
    token = create_access_token(TokenData(user_id=u.id, org_id=u.org_id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def tier_with_modules(db_session):
    """One learning role -> one tier -> two real (non-placeholder) modules."""
    role = LearningRole(name="Test Path", description="", audience="customer", products=["vms"])
    db_session.add(role)
    await db_session.flush()

    tier = Tier(role_id=role.id, label="Foundation", name="Test Path Foundation", cert_name="Test Path Foundation Cert")
    db_session.add(tier)
    await db_session.flush()

    m1 = Module(tier_id=tier.id, title="Module One", module_type="v", duration_mins=5, product="vms", sort_order=1)
    m2 = Module(tier_id=tier.id, title="Module Two", module_type="v", duration_mins=5, product="vms", sort_order=2)
    db_session.add_all([m1, m2])
    await db_session.commit()

    result = await db_session.execute(
        select(Tier).where(Tier.id == tier.id).options(selectinload(Tier.modules))
    )
    return result.scalar_one()
