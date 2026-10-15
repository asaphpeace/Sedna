"""Trained vs untrained support cases, and the Jira sync that feeds them."""
from datetime import datetime, timedelta

import pytest_asyncio
from sqlalchemy import select

from app.models import Module, Organisation, SupportTicket, User, UserModuleProgress
from app.services.jira_tickets import normalise, parse_issue, store
from app.services.ticket_topics import topic_for
from tests.conftest import auth_headers

NOW = datetime.utcnow()


@pytest_asyncio.fixture
async def acme(db_session):
    org = Organisation(name="Acme Bulk AS", slug="acme-bulk", kind="customer")
    db_session.add(org)
    await db_session.flush()
    joined = NOW - timedelta(days=200)
    tara = User(org_id=org.id, email="tara@acme.example", name="Tara", initial="T", status="active", created_at=joined)
    uma = User(org_id=org.id, email="uma@acme.example", name="Uma", initial="U", status="active", created_at=joined)
    db_session.add_all([tara, uma])
    await db_session.commit()
    return {"org": org, "tara": tara, "uma": uma}


# ── Jira parsing and matching ────────────────────────────

def test_parse_issue_reads_only_what_the_measure_needs():
    issue = {"key": "DSD-1", "fields": {
        "summary": "Bunkers on redelivery wrong", "created": "2026-09-01T10:00:00.000+0000",
        "resolutiondate": None, "reporter": {"emailAddress": "Tara@Acme.example"},
        "customfield_10047": {"value": "Acme Bulk|10180"},
    }}
    p = parse_issue(issue, "customfield_10047")
    assert p["customer_name"] == "Acme Bulk"
    assert p["reporter_email"] == "tara@acme.example"
    assert p["created_at"] == datetime(2026, 9, 1, 10, 0)
    assert topic_for(p["title"]) == "Bunkers"


def test_company_names_match_across_suffixes():
    assert normalise("Acme Bulk AS") == normalise("ACME BULK") == "acme bulk"


async def test_store_matches_company_and_learner(db_session, acme, admin):
    parsed = [
        {"external_ref": "DSD-1", "customer_name": "ACME Bulk", "reporter_email": "tara@acme.example",
         "title": "Laytime invoicing error", "created_at": NOW - timedelta(days=5), "resolved_at": None},
        {"external_ref": "DSD-2", "customer_name": "Acme Bulk", "reporter_email": None,
         "title": "Invoice not posting", "created_at": NOW - timedelta(days=4), "resolved_at": None},
        # Raised by a Sedna colleague: counts for the company, not for a learner
        {"external_ref": "DSD-3", "customer_name": "Acme Bulk", "reporter_email": "admin@example.com",
         "title": "Slow system", "created_at": NOW - timedelta(days=3), "resolved_at": None},
        {"external_ref": "DSD-4", "customer_name": "Someone Else", "reporter_email": None,
         "title": "Other", "created_at": NOW - timedelta(days=2), "resolved_at": None},
    ]
    counts = await store(db_session, parsed)
    assert counts == {"cases": 4, "company": 3, "person": 1}

    # Re-running updates in place
    await store(db_session, parsed)
    rows = (await db_session.execute(select(SupportTicket))).scalars().all()
    assert len(rows) == 4
    assert {r.external_ref: r.topic for r in rows}["DSD-1"] == "Laytime and demurrage"


# ── The comparison ───────────────────────────────────────

async def test_cases_are_split_at_the_point_someone_is_trained(client, db_session, acme, admin, tier_with_modules):
    tara, uma, org = acme["tara"], acme["uma"], acme["org"]
    org_id, tara_id, uma_id = org.id, tara.id, uma.id
    nassia = auth_headers(admin)

    # Tara finishes 3 lessons 60 days ago, so she's trained for the last 60 days
    for i in range(1, 2):
        db_session.add(Module(tier_id=tier_with_modules.id, title=f"Extra {i}", module_type="a", sort_order=10 + i))
    await db_session.commit()
    lessons = (await db_session.execute(select(Module).where(Module.tier_id == tier_with_modules.id))).scalars().all()
    trained_at = NOW - timedelta(days=60)
    for m in lessons[:3]:
        db_session.add(UserModuleProgress(user_id=tara_id, module_id=m.id, state="done", pct_complete=100,
                                          started_at=trained_at - timedelta(days=1), completed_at=trained_at))

    def case(ref, uid, days_ago):
        return SupportTicket(external_ref=ref, org_id=org_id, user_id=uid, title="x", topic="Bunkers",
                             created_at=NOW - timedelta(days=days_ago))
    db_session.add_all([
        case("DSD-10", tara_id, 120), case("DSD-11", tara_id, 100), case("DSD-12", tara_id, 90),  # Tara untrained
        case("DSD-13", tara_id, 20),                                                            # Tara trained
        case("DSD-14", uma_id, 50), case("DSD-15", uma_id, 40), case("DSD-17", uma_id, 150),     # Uma, never trained
        case("DSD-18", uma_id, 130), case("DSD-19", uma_id, 110), case("DSD-20", uma_id, 70),
        case("DSD-16", None, 30),                                                                # no person matched
    ])
    await db_session.commit()

    data = (await client.get("/analytics/impact?period=12m&audience=customer", headers=nassia)).json()["support"]
    assert data["has_tickets"] and data["companies_compared"] == 1
    assert data["tickets"] == 11 and data["matched_to_person"] == 10
    assert data["trained"]["tickets"] == 1 and data["untrained"]["tickets"] == 9
    # Trained time ≈ 60 days (≈2 months); untrained ≈ 140 days for Tara + 200 for Uma
    assert 1.8 < data["trained"]["user_months"] < 2.2
    assert data["trained"]["rate"] < data["untrained"]["rate"]
    assert data["difference_pct"] < 0
    assert data["too_early"] is True  # far less than 6 user-months of trained time
    assert data["topics"][0] == {"topic": "Bunkers", "tickets": 11}


async def test_no_tickets_means_no_comparison(client, acme, admin):
    data = (await client.get("/analytics/impact?period=12m", headers=auth_headers(admin))).json()["support"]
    assert data["has_tickets"] is False
