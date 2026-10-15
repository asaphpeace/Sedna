"""Build (or rebuild) the demo database: real course catalogue, fictional people.

The demo database is separate from the real one, so nothing here can touch real
learners. Each run wipes it, copies today's course catalogue from the real
database, then generates fictional companies, learners and about six months of
learning activity so the Learning impact dashboard shows realistic patterns.

Run with the demo stack (see docker-compose.yml, profile "demo"):

    docker compose --profile demo run --rm demo-backend python -m app.demo_seed

Demo sign-in (test values for this local demo only):
    demo-admin@sedna.example  /  demo-password
Every fictional learner also uses demo-password.

The generation is seeded, so every run tells the same story; dates are
relative to today, so the activity always ends "now".
"""
import asyncio
import os
import random
from datetime import datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import Base
from app.models import *  # noqa: F401,F403 — registers all models with Base
from app.services.auth import hash_password

DEMO_PASSWORD = "demo-password"
DAYS_OF_HISTORY = 185  # six months, so 'last quarter' has a full quarter before it

# Content tables copied as-is from the real database, parents first
CONTENT_TABLES = ["learning_roles", "tiers", "modules", "quiz_questions", "quiz_options", "releases", "badges"]

# In the demo, customers can take these paths. In the real catalogue they are
# staff-only for now; making customer versions is Becki and Nassia's decision.
CUSTOMER_PATHS = ["Shipping from Scratch", "Sedna Email"]
STAFF_PATHS = ["Employee Onboarding", "Shipping from Scratch", "VMS Support", "Sedna Email", "Sedna Email Support"]

# Fictional companies — invented names, not real shipping firms
COMPANIES = [
    {"name": "Sedna", "slug": "sedna", "kind": "sedna", "people": 16, "keen": 0.85, "domain": "sedna.example"},
    {"name": "Aldermoor Tankers", "slug": "aldermoor-tankers", "kind": "customer", "people": 12, "keen": 0.75, "domain": "aldermoor.example"},
    {"name": "Brightwater Bulk", "slug": "brightwater-bulk", "kind": "customer", "people": 10, "keen": 0.6, "domain": "brightwater.example"},
    {"name": "Kestrel Line", "slug": "kestrel-line", "kind": "customer", "people": 8, "keen": 0.45, "domain": "kestrel.example"},
    {"name": "Orrin Chartering", "slug": "orrin-chartering", "kind": "customer", "people": 6, "keen": 0.3, "domain": "orrin.example"},
]
STAFF_ROLES = ["Support Engineer", "Solution Consultant", "Implementation Consultant", "Customer Success Manager", "Account Executive"]
CUSTOMER_ROLES = ["Chartering Manager", "Operator", "Laytime Analyst", "Marine Accountant", "Trader"]
FIRST = ["Ana", "Ben", "Chloe", "Dimitri", "Elena", "Femi", "Grace", "Hamid", "Ines", "Jonas", "Kofi", "Lena", "Marco",
         "Nadia", "Omar", "Priya", "Quentin", "Rosa", "Sven", "Tara", "Umar", "Vera", "Wei", "Xenia", "Yusuf", "Zoe"]
LAST = ["Andersen", "Barros", "Costa", "Dahl", "Evans", "Fischer", "Georgiou", "Haddad", "Ivanova", "Jensen", "Kim",
        "Larsen", "Mensah", "Nakamura", "Okafor", "Petrov", "Quinn", "Rossi", "Silva", "Tanaka", "Ueda", "Varga",
        "Walsh", "Xu", "Yilmaz", "Zielinski"]
COLORS = ["#7A3FE5", "#0B8FB0", "#0E9E6E", "#B26A00", "#B0322B", "#4B1FA8"]

# Fictional support cases for customer learners, so the trained vs untrained
# comparison has something to show. Untrained people raise cases at roughly
# twice the rate of trained ones, which is the kind of gap the real measure
# looks for; it is an assumption for the demo, not a finding.
CASES_PER_MONTH_UNTRAINED = 0.9
CASES_PER_MONTH_TRAINED = 0.45
SHARE_WITH_REPORTER_EMAIL = 0.7
DEMO_CASE_TITLES = {
    "Invoicing, costs and accounting": ["Freight still pending after invoicing", "Cannot assemble invoice", "Accruals counted twice"],
    "Voyages and port calls": ["Voyage start date picked from old voyage", "Wrong distance between ports", "Port call status colours"],
    "Bunkers": ["Negative ROB after bunkering", "Bunkers on redelivery not in SOA", "Bunker cost wrong in P&L"],
    "Hire, TC and statements of account": ["Hire invoice shows wrong days", "Statement of account changed lines"],
    "Laytime and demurrage": ["Agreed demurrage not in receivables", "Reversible laytime question"],
    "Users, sign-in and access": ["User cannot log in", "Change user permissions"],
}


def _demo_url() -> str:
    url = settings.database_url
    if not url.rsplit("/", 1)[-1].endswith("_demo"):
        raise SystemExit(f"Refusing to run: DATABASE_URL must point at a *_demo database, not {url.rsplit('/', 1)[-1]}")
    return url


def _source_url(demo_url: str) -> str:
    return os.environ.get("SOURCE_DATABASE_URL") or demo_url.rsplit("/", 1)[0] + "/" + demo_url.rsplit("/", 1)[-1][: -len("_demo")]


async def _ensure_database(demo_url: str):
    admin = create_async_engine(demo_url.rsplit("/", 1)[0] + "/postgres", isolation_level="AUTOCOMMIT")
    name = demo_url.rsplit("/", 1)[-1]
    async with admin.connect() as conn:
        exists = await conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": name})
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{name}"'))
            print(f"Created database {name}.")
    await admin.dispose()


async def _copy_catalogue(source_url: str, demo_engine):
    source = create_async_engine(source_url)
    tables = {t.name: t for t in Base.metadata.sorted_tables}
    async with source.connect() as src, demo_engine.begin() as dst:
        for name in CONTENT_TABLES:
            table = tables[name]
            rows = [dict(r._mapping) for r in (await src.execute(select(table))).all()]
            if rows:
                await dst.execute(table.insert(), rows)
                await dst.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{name}', 'id'), (SELECT MAX(id) FROM {name}))"
                ))
            print(f"  copied {len(rows):>4} {name}")
    await source.dispose()


def _lessons_by_path(rows) -> dict[str, list[tuple]]:
    """Path name -> [(tier, module), ...] in learning order, real lessons only."""
    out: dict[str, list[tuple]] = {}
    for module, tier, role in sorted(rows, key=lambda r: (r[2].id, r[1].sort_order, r[0].sort_order)):
        out.setdefault(role.name, []).append((tier, module))
    return out


_case_no = 0


def _support_cases(db, rng, user, joined, completions, start_of_history, now) -> int:
    """Raise cases at the untrained rate until the person's third finished
    lesson and at the trained rate after it. Each stretch gets its expected
    number of cases (rounded at random) scattered across it, rather than a
    day-by-day coin toss, so a small demo doesn't swing on luck."""
    global _case_no
    trained_from = sorted(completions)[2] if len(completions) >= 3 else None
    begin = max(joined, start_of_history - timedelta(days=60))
    cut = min(max(trained_from, begin), now) if trained_from else now
    stretches = [(begin, cut, CASES_PER_MONTH_UNTRAINED), (cut, now, CASES_PER_MONTH_TRAINED)]
    made = 0
    for s_from, s_to, rate in stretches:
        days = (s_to - s_from).total_seconds() / 86400
        if days <= 0:
            continue
        count = int(rate * days / 30.44 + rng.random())
        # The same even split for which cases carry a reporter email
        with_email = int(count * SHARE_WITH_REPORTER_EMAIL + rng.random())
        for n in range(count):
            topic = rng.choice(list(DEMO_CASE_TITLES))
            _case_no += 1
            matched = n < with_email
            db.add(SupportTicket(
                external_ref=f"DEMO-{_case_no:05d}", org_id=user.org_id,
                customer_name=None, reporter_email=user.email if matched else None,
                user_id=user.id if matched else None,
                title=rng.choice(DEMO_CASE_TITLES[topic]), topic=topic,
                created_at=s_from + timedelta(days=rng.uniform(0, days)),
            ))
            made += 1
    return made


async def _generate(db: AsyncSession, rng: random.Random, now: datetime):
    rows = (await db.execute(
        select(Module, Tier, LearningRole)
        .join(Tier, Module.tier_id == Tier.id)
        .join(LearningRole, Tier.role_id == LearningRole.id)
        .where(Module.is_placeholder == False)
    )).all()
    lessons = _lessons_by_path(rows)
    roles = {r[2].name: r[2] for r in rows}
    for name in CUSTOMER_PATHS:
        if name in roles:
            roles[name].audience = "customer"

    password = hash_password(DEMO_PASSWORD)
    start_of_history = now - timedelta(days=DAYS_OF_HISTORY)
    used_names: set[str] = set()
    cred = 10_000_000
    totals = {"people": 0, "lessons": 0, "certificates": 0, "cases": 0}

    for company in COMPANIES:
        org = Organisation(name=company["name"], slug=company["slug"], kind=company["kind"])
        db.add(org)
        await db.flush()

        if company["kind"] == "sedna":
            db.add(User(
                org_id=org.id, email="demo-admin@sedna.example", name="Demo Admin", initial="D",
                role="Education", status="active", is_admin=True, password_hash=password,
                created_at=start_of_history - timedelta(days=30),
            ))

        for i in range(company["people"]):
            while True:
                name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
                if name not in used_names:
                    used_names.add(name)
                    break
            staff = company["kind"] == "sedna"
            # Adoption grows: a third were here before the window, the rest are
            # invited during it, more of them in recent weeks
            joined = start_of_history - timedelta(days=rng.randint(0, 60)) if rng.random() < 0.33 \
                else start_of_history + timedelta(days=(DAYS_OF_HISTORY - 7) * rng.random() ** 0.6)
            user = User(
                org_id=org.id,
                email=f"{name.lower().replace(' ', '.')}@{company['domain']}",
                name=name, initial=name[0], color=rng.choice(COLORS),
                role=rng.choice(STAFF_ROLES if staff else CUSTOMER_ROLES),
                status="active", is_admin=False, password_hash=password, created_at=joined,
            )
            db.add(user)
            await db.flush()
            totals["people"] += 1

            # Not everyone takes part: how keen a company is sets its coverage
            if rng.random() > company["keen"]:
                if not staff:
                    totals["cases"] += _support_cases(db, rng, user, joined, [], start_of_history, now)
                continue

            pool = [p for p in (STAFF_PATHS if staff else CUSTOMER_PATHS) if p in lessons]
            if staff and "Employee Onboarding" in pool:
                chosen = ["Employee Onboarding"] + rng.sample([p for p in pool if p != "Employee Onboarding"], k=rng.randint(0, 2))
            else:
                chosen = rng.sample(pool, k=rng.randint(1, len(pool)))

            last_seen = None
            completions: list[datetime] = []
            for path in chosen:
                # People already here start whenever in the window; new joiners start within two weeks
                if joined < start_of_history:
                    t = start_of_history + timedelta(days=rng.uniform(-30, DAYS_OF_HISTORY - 3), hours=rng.uniform(8, 17))
                else:
                    t = joined + timedelta(days=rng.uniform(0, 14), hours=rng.uniform(8, 17))
                pace = rng.uniform(0.3, 3.5)            # days between lessons
                stamina = rng.uniform(0.88, 0.995)      # chance of carrying on to the next lesson
                for idx, (tier, module) in enumerate(lessons[path]):
                    if t >= now:
                        break
                    # Long paths lose people around a third of the way in
                    hard = 0.12 if (len(lessons[path]) > 20 and idx == len(lessons[path]) // 3) else 0.0
                    started = t
                    mins = max(module.duration_mins or 0, 4)
                    finished = started + timedelta(minutes=mins * rng.uniform(1.0, 2.5))
                    if finished >= now or rng.random() > stamina - hard:
                        # Opened but never finished: this is where they stopped
                        db.add(UserModuleProgress(user_id=user.id, module_id=module.id, state="in_progress",
                                                  pct_complete=rng.choice([10, 25, 40]), started_at=started))
                        db.add(ActivityLog(user_id=user.id, action="started", target_type="module",
                                           target_id=module.id, target_label=module.title, created_at=started))
                        db.add(LearningTime(user_id=user.id, module_id=module.id, day=started.date(),
                                            seconds=int(mins * 60 * rng.uniform(0.2, 0.6))))
                        last_seen = max(filter(None, [last_seen, started]))
                        break
                    db.add(UserModuleProgress(user_id=user.id, module_id=module.id, state="done", pct_complete=100,
                                              started_at=started, completed_at=finished))
                    db.add(ActivityLog(user_id=user.id, action="completed", target_type="module",
                                       target_id=module.id, target_label=module.title, created_at=finished))
                    db.add(LearningTime(user_id=user.id, module_id=module.id, day=started.date(),
                                        seconds=int(mins * 60 * rng.uniform(0.8, 1.6))))
                    totals["lessons"] += 1
                    completions.append(finished)
                    last_seen = max(filter(None, [last_seen, finished]))

                    # Last lesson of a tier earns its certificate
                    tier_lessons = [m for tr, m in lessons[path] if tr.id == tier.id]
                    if module.id == tier_lessons[-1].id:
                        cred += rng.randint(1, 999)
                        db.add(Certificate(user_id=user.id, tier_id=tier.id, credential_number=f"SA-{cred}",
                                           issued_at=finished))
                        db.add(ActivityLog(user_id=user.id, action="earned", target_type="tier",
                                           target_id=tier.id, target_label=tier.cert_name, created_at=finished))
                        totals["certificates"] += 1

                    t = finished + timedelta(days=rng.expovariate(1 / pace), hours=rng.uniform(-3, 3))
            user.last_active_at = last_seen
            if not staff:
                totals["cases"] += _support_cases(db, rng, user, joined, completions, start_of_history, now)
            await db.flush()

    await db.commit()
    print(f"  {totals['people']} fictional learners in {len(COMPANIES)} companies, "
          f"{totals['lessons']} lessons completed, {totals['certificates']} certificates, "
          f"{totals['cases']} support cases")


async def main():
    demo_url = _demo_url()
    await _ensure_database(demo_url)
    engine = create_async_engine(demo_url)

    print("Resetting demo database…")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    print("Copying the course catalogue from the real database…")
    await _copy_catalogue(_source_url(demo_url), engine)

    print("Generating fictional learners and activity…")
    now = datetime.utcnow()
    rng = random.Random("sedna-demo")
    async with async_sessionmaker(engine, expire_on_commit=False)() as db:
        await _generate(db, rng, now)
    await engine.dispose()
    print("✓ Demo ready at http://localhost:5176 — sign in as demo-admin@sedna.example")


if __name__ == "__main__":
    asyncio.run(main())
