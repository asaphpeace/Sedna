"""
One-time production bootstrap: creates all tables and (optionally) the first
admin user + organisation.

Run once after the first deploy:
    docker compose -f docker-compose.prod.yml exec backend python -m app.init_db

Set ADMIN_EMAIL / ADMIN_PASSWORD / ADMIN_NAME / ORG_NAME env vars to also
create the first admin account in the same run. Safe to re-run — it will not
duplicate tables or the admin user.
"""
import asyncio
import os

from sqlalchemy import select

from app.database import AsyncSessionLocal, Base, engine
from app.models import *  # noqa: F401,F403 — registers all models with Base
from app.models.user import Organisation, User
from app.services.auth import hash_password


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created (or already existed).")

    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    admin_name = os.environ.get("ADMIN_NAME", "Admin")
    org_name = os.environ.get("ORG_NAME", "Sedna Academy")

    if not admin_email or not admin_password:
        print("ADMIN_EMAIL / ADMIN_PASSWORD not set — skipping admin user creation.")
        return

    async with AsyncSessionLocal() as db:
        existing = (
            await db.execute(select(User).where(User.email == admin_email))
        ).scalar_one_or_none()
        if existing:
            print(f"Admin user {admin_email} already exists — skipping.")
            return

        org = Organisation(name=org_name, slug=org_name.lower().replace(" ", "-"))
        db.add(org)
        await db.flush()

        admin = User(
            org_id=org.id,
            email=admin_email,
            name=admin_name,
            initial=admin_name[0].upper(),
            role="Admin",
            status="active",
            password_hash=hash_password(admin_password),
            is_admin=True,
        )
        db.add(admin)
        await db.commit()
        print(f"Created organisation '{org_name}' and admin user {admin_email}.")


if __name__ == "__main__":
    asyncio.run(main())
