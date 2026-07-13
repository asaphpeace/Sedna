from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.release import Release
from app.models.user import User
from app.schemas.release import ReleaseOut
from app.services.deps import current_user

router = APIRouter(prefix="/releases", tags=["releases"])


@router.get("", response_model=list[ReleaseOut])
async def list_releases(
    product: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    q = select(Release).order_by(Release.published_at.desc())
    if product:
        q = q.where(Release.product == product)
    result = await db.execute(q)
    return result.scalars().all()
