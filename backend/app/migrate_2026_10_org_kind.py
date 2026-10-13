"""Add organisations.kind ("sedna" | "customer"), mark Sedna's own organisation,
and create the learning_time table.

create_all() only creates missing tables, so existing databases need this
column added by hand. Safe to re-run.

    docker compose exec backend python -m app.migrate_2026_10_org_kind [org-slug]

The slug names Sedna's staff organisation. Leave it out when the database has
exactly one organisation and that one is marked.
"""
import asyncio
import sys

from sqlalchemy import text

from app.database import Base, engine
from app.models import *  # noqa: F401,F403 — registers all models with Base


async def main(slug: str | None):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text(
            "ALTER TABLE organisations ADD COLUMN IF NOT EXISTS kind VARCHAR(20) NOT NULL DEFAULT 'customer'"
        ))
        orgs = (await conn.execute(text("SELECT id, slug, kind FROM organisations ORDER BY id"))).all()
        if slug is None:
            if len(orgs) != 1:
                print("More than one organisation — pass the slug of Sedna's own:", ", ".join(o.slug for o in orgs))
                return
            slug = orgs[0].slug
        result = await conn.execute(text("UPDATE organisations SET kind = 'sedna' WHERE slug = :slug"), {"slug": slug})
        print(f"Marked '{slug}' as Sedna staff." if result.rowcount else f"No organisation with slug '{slug}'.")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else None))
