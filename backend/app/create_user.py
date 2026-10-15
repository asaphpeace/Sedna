"""Create a sign-in for someone directly, when invite emails can't be sent
(e.g. a local preview with email switched off). The password is typed at a
prompt, never passed on the command line, and only its hash is stored.

    docker compose exec backend python -m app.create_user nassia@sedna.com "Nassia Katroutsou" --admin

Adds them to Sedna's own organisation unless --org <slug> names another.
"""
import argparse
import asyncio
import getpass
import random
import sys

from sqlalchemy import func, select

from app.database import AsyncSessionLocal
from app.models import *  # noqa: F401,F403 — registers all models
from app.models.user import Organisation, User
from app.services.accounts import COLORS
from app.services.auth import hash_password


def _ask_password() -> str:
    while True:
        first = getpass.getpass("Password (at least 8 characters): ")
        if len(first) < 8:
            print("Too short, try again.")
            continue
        if getpass.getpass("Same password again: ") != first:
            print("They don't match, try again.")
            continue
        return first


async def main(email: str, name: str, org_slug: str | None, is_admin: bool, role: str | None):
    async with AsyncSessionLocal() as db:
        if await db.scalar(select(User.id).where(func.lower(User.email) == email.lower())):
            sys.exit(f"{email} already has an account.")
        q = select(Organisation).where(Organisation.slug == org_slug) if org_slug \
            else select(Organisation).where(Organisation.kind == "sedna")
        orgs = (await db.execute(q)).scalars().all()
        if len(orgs) != 1:
            sys.exit("Couldn't pick one organisation; pass --org <slug>.")
        password = _ask_password()
        db.add(User(
            org_id=orgs[0].id, email=email, name=name, initial=name[0].upper(),
            color=random.choice(COLORS), role=role, status="active", is_admin=is_admin,
            password_hash=hash_password(password),
        ))
        await db.commit()
        print(f"Created {name} <{email}> in {orgs[0].name}{' as an admin' if is_admin else ''}.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("email")
    p.add_argument("name")
    p.add_argument("--org", dest="org_slug")
    p.add_argument("--admin", action="store_true")
    p.add_argument("--role")
    a = p.parse_args()
    asyncio.run(main(a.email, a.name, a.org_slug, a.admin, a.role))
