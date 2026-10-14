"""Who may see which part of the shared course catalogue.

Sedna staff see every published path. Customers see only published customer
paths. Draft paths and draft lessons (placeholder outlines included) are
visible only to Sedna admins, who author them.
"""
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import LearningRole, Module, Tier
from app.models.user import User
from app.services.deps import is_sedna_staff


@dataclass
class Viewer:
    staff: bool
    sees_drafts: bool

    def can_see_path(self, role: LearningRole) -> bool:
        if not role.is_published and not self.sees_drafts:
            return False
        return self.staff or role.audience == "customer"


async def viewer(db: AsyncSession, user: User) -> Viewer:
    staff = await is_sedna_staff(db, user)
    return Viewer(staff=staff, sees_drafts=staff and user.is_admin)


async def require_module_visible(db: AsyncSession, user: User, module_id: int) -> Module:
    """404 (not 403, so nothing leaks about what exists) unless the user may see this lesson."""
    row = (await db.execute(
        select(Module, LearningRole)
        .join(Tier, Module.tier_id == Tier.id)
        .join(LearningRole, Tier.role_id == LearningRole.id)
        .where(Module.id == module_id)
    )).first()
    v = await viewer(db, user)
    if not row or not v.can_see_path(row.LearningRole) or (row.Module.is_placeholder and not v.sees_drafts):
        raise HTTPException(status_code=404, detail="Module not found")
    return row.Module
