"""Create the articles table (Knowledge Base and Help Center). Safe to re-run.

    docker compose exec backend python -m app.migrate_2026_10_articles
"""
import asyncio

from app.database import Base, engine
from app.models import *  # noqa: F401,F403 — registers all models with Base


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("articles table is in place.")


if __name__ == "__main__":
    asyncio.run(main())
