"""Google sign-in: check a Google ID token, then decide who it lets in.

Who may sign in with Google:
- Staff: a Google Workspace account on one of settings.staff_google_domains
  (sedna.com). No invite needed; a first sign-in creates a staff learner.
- Customers: a Workspace account on one of settings.customer_google_domains,
  and only if they were already invited. Customers never self-register.

Both require Google's `hd` (hosted domain) claim to match the email's
domain, so a personal Google account registered with a work address
doesn't count as the company's Workspace account.
"""
import random
import time

import httpx
from fastapi import HTTPException
from jose import JWTError, jwt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import Organisation, User
from app.services.accounts import COLORS

GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}

_certs: dict = {}
_certs_expire_at = 0.0


async def _google_keys() -> dict:
    global _certs, _certs_expire_at
    if not _certs or time.time() > _certs_expire_at:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(GOOGLE_CERTS_URL)
            resp.raise_for_status()
        _certs = resp.json()
        _certs_expire_at = time.time() + 3600  # Google rotates keys rarely; refetch hourly
    return _certs


async def verify_google_token(credential: str) -> dict:
    """Return the token's claims if Google signed it for our client ID."""
    try:
        claims = jwt.decode(
            credential, await _google_keys(), algorithms=["RS256"],
            audience=settings.google_client_id, options={"verify_at_hash": False},
        )
    except (JWTError, httpx.HTTPError):
        raise HTTPException(status_code=401, detail="Google sign-in couldn't be verified. Try again.")
    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise HTTPException(status_code=401, detail="Google sign-in couldn't be verified. Try again.")
    return claims


async def user_for_google(db: AsyncSession, claims: dict) -> User:
    """Apply the sign-in rules and return the person to sign in."""
    email = (claims.get("email") or "").strip().lower()
    domain = email.rpartition("@")[2]
    staff_domain = domain in settings.staff_google_domains
    customer_domain = domain in settings.customer_google_domains
    not_allowed = HTTPException(
        status_code=403,
        detail="Google sign-in isn't available for this account. Sign in with your email and password, or ask your Sedna contact.",
    )
    if not email or not claims.get("email_verified") or not (staff_domain or customer_domain):
        raise not_allowed
    if (claims.get("hd") or "").lower() != domain:
        raise not_allowed

    user = await db.scalar(select(User).where(func.lower(User.email) == email))
    if user:
        if user.status not in ("active", "invited"):
            raise not_allowed
        if user.status == "invited":
            user.status = "active"
            user.invite_token = None
            user.invite_token_expires_at = None
            await db.commit()
        return user

    if not staff_domain:
        # Customers are invite-only
        raise not_allowed
    orgs = (await db.execute(select(Organisation).where(Organisation.kind == "sedna"))).scalars().all()
    if len(orgs) != 1:
        raise HTTPException(status_code=500, detail="Sedna's organisation isn't set up for Google sign-in.")
    name = (claims.get("name") or email.split("@")[0]).strip()
    user = User(
        org_id=orgs[0].id, email=email, name=name, initial=name[0].upper(),
        color=random.choice(COLORS), status="active", is_admin=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
