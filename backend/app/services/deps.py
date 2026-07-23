from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth import decode_token

bearer = HTTPBearer()

# Team/compliance views show "last active" — refresh it on real traffic, but
# throttled so we're not writing to the users row on every single request.
LAST_ACTIVE_THROTTLE = timedelta(minutes=5)


async def current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    token_data = decode_token(creds.credentials)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # DB column is naive (TIMESTAMP WITHOUT TIME ZONE, matching the rest of
    # this codebase's datetime.utcnow() convention) — keep both sides naive.
    now = datetime.utcnow()
    stale = user.last_active_at is None or (now - user.last_active_at > LAST_ACTIVE_THROTTLE)
    if stale:
        user.last_active_at = now
        await db.commit()

    return user


async def admin_user(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    return user


async def manager_or_admin_user(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Admins see the whole org; a department manager sees only their own
    department's compliance/assignment data. Anyone else is rejected."""
    if user.is_admin:
        return user
    from app.models.org_structure import Department  # local import avoids a cycle
    result = await db.execute(select(Department).where(Department.manager_user_id == user.id))
    if result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or manager required")
    return user


async def visible_user_ids(db: AsyncSession, user: User) -> Optional[list[int]]:
    """None means "no restriction" (admin, sees the whole org). Otherwise the
    list of user ids a department manager is allowed to see."""
    if user.is_admin:
        return None
    from app.models.org_structure import Department  # local import avoids a cycle
    dept_result = await db.execute(select(Department).where(Department.manager_user_id == user.id))
    dept_ids = [d.id for d in dept_result.scalars().all()]
    if not dept_ids:
        return []
    members_result = await db.execute(select(User.id).where(User.department_id.in_(dept_ids)))
    return [row[0] for row in members_result.all()]
