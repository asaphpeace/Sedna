"""Add learning_roles.is_published. Every existing path stays published.

create_all() only creates missing tables, so existing databases need this
column added by hand. Safe to re-run.

    docker compose exec backend python -m app.migrate_2026_10_path_published
"""
import asyncio

from sqlalchemy import text

from app.database import engine


async def main():
    async with engine.begin() as conn:
        await conn.execute(text(
            "ALTER TABLE learning_roles ADD COLUMN IF NOT EXISTS is_published BOOLEAN NOT NULL DEFAULT true"
        ))
    print("learning_roles.is_published is in place; existing paths stay published.")


if __name__ == "__main__":
    asyncio.run(main())
