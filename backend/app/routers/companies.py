"""Companies (organisations) and the people in them.

Sedna admins set up customer companies and invite people into any of them.
A company's own admin manages only their company — through /team — and can
remove its learners here, but never sees or touches another company.
"""
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import Organisation, User
from app.schemas.user import UserOut
from app.services import accounts
from app.services.deps import admin_user, is_sedna_staff, sedna_admin_user

router = APIRouter(prefix="/admin", tags=["companies"])


class CompanyOut(BaseModel):
    id: int
    name: str
    kind: str
    people: int
    admins: int


class CompanyIn(BaseModel):
    name: str = Field(min_length=2, max_length=255)


class CompanyInvite(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)
    role: Optional[str] = None
    is_admin: bool = False


async def _company(db: AsyncSession, org_id: int) -> Organisation:
    org = await db.get(Organisation, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Company not found")
    return org


@router.get("/companies", response_model=list[CompanyOut])
async def list_companies(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(sedna_admin_user),
):
    counts = dict((await db.execute(
        select(User.org_id, func.count()).where(User.status != "removed").group_by(User.org_id)
    )).all())
    admins = dict((await db.execute(
        select(User.org_id, func.count()).where(User.status != "removed", User.is_admin == True).group_by(User.org_id)
    )).all())
    orgs = (await db.execute(select(Organisation))).scalars().all()
    # Sedna first, then customers by name
    orgs.sort(key=lambda o: (o.kind != "sedna", o.name.lower()))
    return [
        CompanyOut(id=o.id, name=o.name, kind=o.kind, people=counts.get(o.id, 0), admins=admins.get(o.id, 0))
        for o in orgs
    ]


@router.post("/companies", response_model=CompanyOut)
async def create_company(
    body: CompanyIn,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(sedna_admin_user),
):
    name = body.name.strip()
    if await db.scalar(select(Organisation.id).where(func.lower(Organisation.name) == name.lower())):
        raise HTTPException(status_code=409, detail="A company with that name already exists")
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "company"
    slug, n = base, 2
    while await db.scalar(select(Organisation.id).where(Organisation.slug == slug)):
        slug, n = f"{base}-{n}", n + 1
    # New companies are always customers; there is one Sedna organisation
    org = Organisation(name=name, slug=slug, kind="customer")
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return CompanyOut(id=org.id, name=org.name, kind=org.kind, people=0, admins=0)


@router.get("/companies/{org_id}/users", response_model=list[UserOut])
async def company_users(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(sedna_admin_user),
):
    await _company(db, org_id)
    return (await db.execute(
        select(User).where(User.org_id == org_id, User.status != "removed").order_by(User.name)
    )).scalars().all()


@router.post("/companies/{org_id}/invite", response_model=UserOut)
async def invite_to_company(
    org_id: int,
    body: CompanyInvite,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(sedna_admin_user),
):
    org = await _company(db, org_id)
    return await accounts.invite(db, org, admin, body.email, body.name, body.role, body.is_admin)


@router.delete("/users/{user_id}", status_code=204)
async def remove_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_user),
):
    """Remove someone on request (GDPR): anonymised, not deleted, so their
    completions still count in totals. Sedna admins can remove anyone; a
    company's admin only people in their own company."""
    target = await db.get(User, user_id)
    allowed = target is not None and target.status != "removed" and (
        target.org_id == admin.org_id or await is_sedna_staff(db, admin)
    )
    if not allowed:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="You can't remove your own account")
    await accounts.anonymise(db, target)
