"""Sync VMS support cases from Jira for the customer impact measures.

Read-only against Jira: one paginated JQL search over the support project,
asking only for the fields the measures use (summary, created, resolution
date, reporter, Customer). Each case is matched to a Hub company by the Jira
"Customer" name, and to a learner by the reporter's email.

Jira only exposes an email for portal-customer accounts, not for every
reporter, so some cases match a company but no person. The dashboard reports
how many matched at each level rather than hiding the gap.
"""
import re
from datetime import datetime

import httpx
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.progress import SupportTicket
from app.models.user import Organisation, User
from app.services.ticket_topics import topic_for

_SUFFIXES = re.compile(r"\b(as|asa|ab|aps|bv|b v|gmbh|ltd|limited|inc|llc|plc|sa|s a|pte|co|company|group|shipping)\b")


class JiraNotConfigured(Exception):
    pass


def normalise(name: str | None) -> str:
    """Company names differ in suffixes and punctuation between Jira and the Hub."""
    value = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower())
    value = _SUFFIXES.sub(" ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_issue(issue: dict, customer_field: str) -> dict:
    f = issue.get("fields") or {}
    customer = (f.get(customer_field) or {}).get("value") or ""
    reporter = f.get("reporter") or {}
    email = (reporter.get("emailAddress") or "").strip().lower() or None

    def ts(value):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None) if value else None

    return {
        "external_ref": issue["key"],
        "customer_name": customer.split("|")[0].strip() or None,
        "reporter_email": email,
        "title": (f.get("summary") or "")[:500],
        "created_at": ts(f.get("created")),
        "resolved_at": ts(f.get("resolutiondate")),
    }


async def fetch_issues(since_days: int) -> list[dict]:
    if not (settings.jira_base_url and settings.jira_email and settings.jira_api_token):
        raise JiraNotConfigured("Set JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN in backend/.env")
    url = f"{settings.jira_base_url.rstrip('/')}/rest/api/3/search/jql"
    jql = f'project = "{settings.jira_project}" AND created >= -{since_days}d ORDER BY created ASC'
    fields = f"summary,created,resolutiondate,reporter,{settings.jira_customer_field}"
    issues, token = [], None
    auth = httpx.BasicAuth(settings.jira_email, settings.jira_api_token)
    async with httpx.AsyncClient(auth=auth, timeout=30, follow_redirects=True) as client:
        while True:
            params = {"jql": jql, "maxResults": 100, "fields": fields}
            if token:
                params["nextPageToken"] = token
            resp = await client.get(url, headers={"Accept": "application/json"}, params=params)
            resp.raise_for_status()
            data = resp.json()
            issues.extend(data.get("issues", []))
            token = data.get("nextPageToken")
            if data.get("isLast", True) or not token:
                break
    return issues


async def store(db: AsyncSession, parsed: list[dict]) -> dict:
    """Upsert cases and (re)match them to companies and learners."""
    orgs = (await db.execute(select(Organisation).where(Organisation.kind == "customer"))).scalars().all()
    by_name: dict[str, int] = {}
    for o in orgs:
        by_name[normalise(o.name)] = o.id
        if o.jira_name:
            by_name[normalise(o.jira_name)] = o.id
    emails = [p["reporter_email"] for p in parsed if p["reporter_email"]]
    # Only customer learners: a case a Sedna colleague raised on a customer's behalf isn't theirs
    users = (await db.execute(
        select(User.id, User.org_id, func.lower(User.email))
        .where(func.lower(User.email).in_(emails), User.org_id.in_([o.id for o in orgs]))
    )).all() if emails and orgs else []
    user_by_email = {email: (uid, org) for uid, org, email in users}

    counts = {"cases": 0, "company": 0, "person": 0}
    for p in parsed:
        if not p["created_at"]:
            continue
        user_id, org_id = None, by_name.get(normalise(p["customer_name"])) if p["customer_name"] else None
        if p["reporter_email"] in user_by_email:
            user_id, user_org = user_by_email[p["reporter_email"]]
            org_id = org_id or user_org
        row = {**p, "org_id": org_id, "user_id": user_id, "topic": topic_for(p["title"])}
        stmt = pg_insert(SupportTicket).values(**row)
        stmt = stmt.on_conflict_do_update(
            index_elements=["external_ref"],
            set_={k: stmt.excluded[k] for k in row if k != "external_ref"},
        )
        await db.execute(stmt)
        counts["cases"] += 1
        counts["company"] += org_id is not None
        counts["person"] += user_id is not None
    await db.commit()
    return counts


async def sync(db: AsyncSession, since_days: int = 400) -> dict:
    issues = await fetch_issues(since_days)
    return await store(db, [parse_issue(i, settings.jira_customer_field) for i in issues])
