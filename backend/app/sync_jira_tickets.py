"""Pull VMS support cases from Jira into the Hub for the customer impact measures.

    docker compose exec backend python -m app.sync_jira_tickets [days]

Needs JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN in backend/.env (an
Atlassian API token for an account that can read the support project).
Read-only against Jira; safe to re-run, cases are updated in place.
"""
import asyncio
import sys

from app.database import AsyncSessionLocal
from app.services.jira_tickets import JiraNotConfigured, sync


async def main(days: int):
    async with AsyncSessionLocal() as db:
        try:
            counts = await sync(db, since_days=days)
        except JiraNotConfigured as exc:
            print(f"Jira isn't configured: {exc}")
            return
    print(f"Synced {counts['cases']} cases from the last {days} days: "
          f"{counts['company']} matched to a company, {counts['person']} to a learner.")


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 400))
