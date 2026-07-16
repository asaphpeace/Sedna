"""Admin CRUD: paths (learning roles), tiers, modules."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.content import LearningRole, Module, Tier
from app.models.user import User
from app.services.deps import current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return user


# ── Schemas ────────────────────────────────────────────────────────────────

class PathIn(BaseModel):
    name: str
    description: str = ""
    icon: str = "ti-user"
    color: str = "purple"
    audience: str = "customer"
    products: list[str] = []
    sort_order: int = 0


class TierIn(BaseModel):
    label: str
    name: str
    cert_name: str
    sort_order: int = 0


class ModuleIn(BaseModel):
    title: str
    module_type: str = "v"          # v | a | l  (video / article / link)
    duration_mins: int = 0
    product: str = "vms"
    is_placeholder: bool = False
    sort_order: int = 0
    description: str = ""
    learn_items: list[str] = []
    video_url: Optional[str] = None
    transcript: Optional[str] = None
    rich_content: Optional[str] = None  # markdown / plain text


class PathOut(BaseModel):
    id: int
    name: str
    description: str
    icon: str
    color: str
    audience: str
    products: list[str]
    sort_order: int
    tier_count: int
    mod_count: int
    model_config = {"from_attributes": True}


class TierOut(BaseModel):
    id: int
    role_id: int
    label: str
    name: str
    cert_name: str
    sort_order: int
    mod_count: int
    model_config = {"from_attributes": True}


class ModuleOut(BaseModel):
    id: int
    tier_id: int
    title: str
    module_type: str
    duration_mins: int
    product: str
    is_placeholder: bool
    sort_order: int
    description: str
    learn_items: list[str]
    video_url: Optional[str]
    transcript: Optional[str]
    rich_content: Optional[str]
    model_config = {"from_attributes": True}


# ── Paths ──────────────────────────────────────────────────────────────────

@router.get("/paths", response_model=list[PathOut])
async def list_paths(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
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
        out.append(PathOut(
            id=r.id, name=r.name, description=r.description,
            icon=r.icon, color=r.color, audience=r.audience,
            products=r.products, sort_order=r.sort_order,
            tier_count=len(r.tiers), mod_count=mod_count,
        ))
    return out


@router.post("/paths", response_model=PathOut)
async def create_path(
    body: PathIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    role = LearningRole(**body.model_dump())
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return PathOut(
        id=role.id, name=role.name, description=role.description,
        icon=role.icon, color=role.color, audience=role.audience,
        products=role.products, sort_order=role.sort_order,
        tier_count=0, mod_count=0,
    )


@router.patch("/paths/{path_id}", response_model=PathOut)
async def update_path(
    path_id: int,
    body: PathIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(
        select(LearningRole)
        .where(LearningRole.id == path_id)
        .options(selectinload(LearningRole.tiers).selectinload(Tier.modules))
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(404, "Path not found")
    for k, v in body.model_dump().items():
        setattr(role, k, v)
    await db.commit()
    await db.refresh(role)
    mod_count = sum(len(t.modules) for t in role.tiers)
    return PathOut(
        id=role.id, name=role.name, description=role.description,
        icon=role.icon, color=role.color, audience=role.audience,
        products=role.products, sort_order=role.sort_order,
        tier_count=len(role.tiers), mod_count=mod_count,
    )


@router.delete("/paths/{path_id}")
async def delete_path(
    path_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(
        select(LearningRole).where(LearningRole.id == path_id).options(selectinload(LearningRole.tiers))
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(404, "Path not found")
    if role.tiers:
        raise HTTPException(400, "Delete all tiers in this path before deleting the path itself")
    await db.delete(role)
    await db.commit()
    return {"status": "deleted"}


# ── Tiers ──────────────────────────────────────────────────────────────────

@router.get("/paths/{path_id}/tiers", response_model=list[TierOut])
async def list_tiers(
    path_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(
        select(Tier)
        .where(Tier.role_id == path_id)
        .options(selectinload(Tier.modules))
        .order_by(Tier.sort_order)
    )
    tiers = result.scalars().all()
    return [TierOut(
        id=t.id, role_id=t.role_id, label=t.label, name=t.name,
        cert_name=t.cert_name, sort_order=t.sort_order, mod_count=len(t.modules)
    ) for t in tiers]


@router.post("/paths/{path_id}/tiers", response_model=TierOut)
async def create_tier(
    path_id: int,
    body: TierIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    tier = Tier(role_id=path_id, **body.model_dump())
    db.add(tier)
    await db.commit()
    await db.refresh(tier)
    return TierOut(id=tier.id, role_id=tier.role_id, label=tier.label,
                   name=tier.name, cert_name=tier.cert_name,
                   sort_order=tier.sort_order, mod_count=0)


@router.patch("/tiers/{tier_id}", response_model=TierOut)
async def update_tier(
    tier_id: int,
    body: TierIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(
        select(Tier).where(Tier.id == tier_id).options(selectinload(Tier.modules))
    )
    tier = result.scalar_one_or_none()
    if not tier:
        raise HTTPException(404, "Tier not found")
    for k, v in body.model_dump().items():
        setattr(tier, k, v)
    await db.commit()
    await db.refresh(tier)
    return TierOut(id=tier.id, role_id=tier.role_id, label=tier.label,
                   name=tier.name, cert_name=tier.cert_name,
                   sort_order=tier.sort_order, mod_count=len(tier.modules))


@router.delete("/tiers/{tier_id}")
async def delete_tier(
    tier_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(
        select(Tier).where(Tier.id == tier_id).options(selectinload(Tier.modules))
    )
    tier = result.scalar_one_or_none()
    if not tier:
        raise HTTPException(404, "Tier not found")
    if tier.modules:
        raise HTTPException(400, "Delete all modules in this tier before deleting the tier itself")
    await db.delete(tier)
    await db.commit()
    return {"status": "deleted"}


# ── Modules ────────────────────────────────────────────────────────────────

@router.get("/tiers/{tier_id}/modules", response_model=list[ModuleOut])
async def list_tier_modules(
    tier_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(
        select(Module).where(Module.tier_id == tier_id).order_by(Module.sort_order)
    )
    return result.scalars().all()


@router.post("/tiers/{tier_id}/modules", response_model=ModuleOut)
async def create_module(
    tier_id: int,
    body: ModuleIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    mod = Module(tier_id=tier_id, **body.model_dump())
    db.add(mod)
    await db.commit()
    await db.refresh(mod)
    return mod


@router.patch("/modules/{module_id}", response_model=ModuleOut)
async def update_module(
    module_id: int,
    body: ModuleIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(select(Module).where(Module.id == module_id))
    mod = result.scalar_one_or_none()
    if not mod:
        raise HTTPException(404, "Module not found")
    for k, v in body.model_dump().items():
        setattr(mod, k, v)
    await db.commit()
    await db.refresh(mod)
    return mod


@router.delete("/modules/{module_id}")
async def delete_module(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_require_admin),
):
    result = await db.execute(select(Module).where(Module.id == module_id))
    mod = result.scalar_one_or_none()
    if not mod:
        raise HTTPException(404, "Module not found")
    try:
        await db.delete(mod)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Cannot delete: learners have progress or quiz attempts recorded against this module")
    return {"status": "deleted"}
