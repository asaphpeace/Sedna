"""Add users.reset_token_hash and users.reset_token_expires_at for the
forgot-password link. Safe to re-run.

    docker compose exec backend python -m app.migrate_2026_10_password_reset
"""
import asyncio

from sqlalchemy import text

from app.database import engine


async def main():
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_hash VARCHAR(64)"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires_at TIMESTAMP"))
        await conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS users_reset_token_hash_key ON users (reset_token_hash)"
        ))
    print("Password reset columns ready.")


if __name__ == "__main__":
    asyncio.run(main())
