from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.progress import ActivityLog
from app.models.user import User
from app.schemas.progress import ActivityOut
from app.services.deps import current_user

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=list[ActivityOut])
async def org_activity(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(ActivityLog)
        .join(ActivityLog.user)
        .where(User.org_id == user.org_id)
        .options(selectinload(ActivityLog.user))
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
    )
    items = result.scalars().all()
    return [
        ActivityOut(
            id=a.id,
            user_id=a.user_id,
            user_name=a.user.name,
            user_initial=a.user.initial,
            user_color=a.user.color,
            action=a.action,
            target_type=a.target_type,
            target_label=a.target_label,
            created_at=a.created_at,
        )
        for a in items
    ]
