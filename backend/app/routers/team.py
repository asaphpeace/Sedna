from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import Organisation, User
from app.schemas.user import UserOut, UserInvite, UserUpdate
from app.services.deps import current_user, admin_user
from app.services.email import send_invite_email
from app.routers.webhooks import deliver_webhook

router = APIRouter(prefix="/team", tags=["team"])


@router.get("", response_model=list[UserOut])
async def list_team(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(User).where(User.org_id == user.org_id).order_by(User.name)
    )
    return result.scalars().all()


@router.post("/invite", response_model=UserOut)
async def invite_user(
    body: UserInvite,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_user),
):
    import random
    colors = ["#6E2BF0", "#0E9E6E", "#B26A00", "#0B8FB0", "#4338CA"]
    new_user = User(
        org_id=admin.org_id,
        email=body.email,
        name=body.name,
        initial=body.name[0].upper(),
        color=random.choice(colors),
        role=body.role,
        status="invited",
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    org_result = await db.execute(select(Organisation).where(Organisation.id == admin.org_id))
    org = org_result.scalar_one_or_none()
    await send_invite_email(new_user.email, new_user.name, admin.name, org.name if org else "your team")

    await deliver_webhook(db, admin.org_id, "user.invited", {
        "user_id": new_user.id, "email": new_user.email, "invited_by": admin.id,
    })

    return new_user


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
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(target, field, value)
    await db.commit()
    await db.refresh(target)
    return target
