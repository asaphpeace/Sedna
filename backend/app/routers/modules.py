from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.content import Module, Tier
from app.models.user import User
from app.schemas.content import ModuleOut
from app.services.deps import current_user

router = APIRouter(prefix="/modules", tags=["modules"])


def _with_role_id(mod: Module) -> Module:
    # role_id lives on Tier, not Module — stamp it onto the ORM instance so
    # ModuleOut's from_attributes serialization picks it up. Lets the
    # frontend know which path a module belongs to without a second request.
    mod.role_id = mod.tier.role_id  # type: ignore[attr-defined]
    return mod


@router.get("", response_model=list[ModuleOut])
async def browse_modules(
    product: str | None = None,
    module_type: str | None = None,
    tier_id: int | None = None,
    path_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    q = select(Module).options(selectinload(Module.tier))
    if tier_id:
        q = q.where(Module.tier_id == tier_id)
    elif path_id:
        q = q.join(Tier, Module.tier_id == Tier.id).where(Tier.role_id == path_id)
    if product:
        q = q.where(Module.product == product)
    if module_type:
        q = q.where(Module.module_type == module_type)
    q = q.order_by(Module.sort_order)
    result = await db.execute(q)
    return [_with_role_id(m) for m in result.scalars().all()]


@router.get("/{module_id}", response_model=ModuleOut)
async def get_module(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(Module).where(Module.id == module_id).options(selectinload(Module.tier))
    )
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return _with_role_id(module)
