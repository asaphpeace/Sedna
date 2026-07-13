from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.content import Module, Tier, LearningRole
from app.models.progress import SavedModule
from app.models.user import User
from app.schemas.progress import SavedModuleOut
from app.services.deps import current_user

router = APIRouter(prefix="/saved", tags=["saved"])


@router.get("", response_model=list[SavedModuleOut])
async def list_saved(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(SavedModule)
        .where(SavedModule.user_id == user.id)
        .options(selectinload(SavedModule.module).selectinload(Module.tier).selectinload(Tier.role))
        .order_by(SavedModule.saved_at.desc())
    )
    items = result.scalars().all()
    return [
        SavedModuleOut(
            module_id=s.module_id,
            title=s.module.title,
            module_type=s.module.module_type,
            duration_mins=s.module.duration_mins,
            product=s.module.product,
            tier_name=s.module.tier.label,
            role_name=s.module.tier.role.name,
            saved_at=s.saved_at,
        )
        for s in items
    ]


@router.post("/{module_id}")
async def save_module(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    existing = await db.execute(
        select(SavedModule).where(
            SavedModule.user_id == user.id, SavedModule.module_id == module_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already saved")
    db.add(SavedModule(user_id=user.id, module_id=module_id))
    await db.commit()
    return {"status": "ok"}


@router.delete("/{module_id}")
async def unsave_module(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(SavedModule).where(
            SavedModule.user_id == user.id, SavedModule.module_id == module_id
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Not saved")
    await db.delete(item)
    await db.commit()
    return {"status": "ok"}
