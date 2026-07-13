from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.content import LearningRole, Tier, Module
from app.models.user import User
from app.schemas.content import LearningRoleOut, LearningRoleSummary
from app.services.deps import current_user

router = APIRouter(prefix="/paths", tags=["paths"])


@router.get("", response_model=list[LearningRoleSummary])
async def list_paths(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(LearningRole)
        .options(selectinload(LearningRole.tiers).selectinload(Tier.modules))
        .order_by(LearningRole.sort_order)
    )
    roles = result.scalars().all()
    out = []
    for r in roles:
        mod_count = sum(len(t.modules) for t in r.tiers)
        out.append(
            LearningRoleSummary(
                id=r.id, name=r.name, description=r.description,
                icon=r.icon, color=r.color, audience=r.audience,
                products=r.products, mod_count=mod_count, tier_count=len(r.tiers),
            )
        )
    return out


@router.get("/{role_id}", response_model=LearningRoleOut)
async def get_path(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(LearningRole)
        .where(LearningRole.id == role_id)
        .options(selectinload(LearningRole.tiers).selectinload(Tier.modules))
    )
    role = result.scalar_one_or_none()
    if not role:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Path not found")
    return role
