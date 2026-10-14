from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import Organisation, User
from app.schemas.user import UserOut, UserInvite, UserUpdate
from app.services.deps import current_user, admin_user
from app.services import accounts

router = APIRouter(prefix="/team", tags=["team"])


@router.get("", response_model=list[UserOut])
async def list_team(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(User).where(User.org_id == user.org_id, User.status != "removed").order_by(User.name)
    )
    return result.scalars().all()


@router.post("/invite", response_model=UserOut)
async def invite_user(
    body: UserInvite,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_user),
):
    org = await db.get(Organisation, admin.org_id)
    return await accounts.invite(db, org, admin, body.email, body.name, body.role)


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_user),
):
    from fastapi import HTTPException
    result = await db.execute(
        select(User).where(User.id == user_id, User.org_id == admin.org_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if body.status == "removed":
        # Removal has to go through anonymisation, never a bare status flip
        raise HTTPException(status_code=400, detail="Use remove to take someone out of the platform")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(target, field, value)
    await db.commit()
    await db.refresh(target)
    return target
