"""Create the support_tickets table and add organisations.jira_name.

create_all() only creates missing tables, so the new column is added by hand.
Safe to re-run.

    docker compose exec backend python -m app.migrate_2026_10_support_tickets
"""
import asyncio

from sqlalchemy import text

from app.database import Base, engine
from app.models import *  # noqa: F401,F403 — registers all models with Base


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE organisations ADD COLUMN IF NOT EXISTS jira_name VARCHAR(255)"))
    print("support_tickets table and organisations.jira_name are in place.")


if __name__ == "__main__":
    asyncio.run(main())
