from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.settings import NotificationSettings
from app.models.user import User
from app.services.deps import current_user

router = APIRouter(prefix="/settings", tags=["settings"])


class NotificationSettingsOut(BaseModel):
    weekly_digest: bool
    new_modules: bool
    cert_reminders: bool
    product_releases: bool
    team_activity: bool
    marketing_emails: bool

    model_config = {"from_attributes": True}


class NotificationSettingsUpdate(BaseModel):
    weekly_digest: bool | None = None
    new_modules: bool | None = None
    cert_reminders: bool | None = None
    product_releases: bool | None = None
    team_activity: bool | None = None
    marketing_emails: bool | None = None


@router.get("/notifications", response_model=NotificationSettingsOut)
async def get_notification_settings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(NotificationSettings).where(NotificationSettings.user_id == user.id)
    )
    ns = result.scalar_one_or_none()
    if not ns:
        ns = NotificationSettings(user_id=user.id)
        db.add(ns)
        await db.commit()
        await db.refresh(ns)
    return ns


@router.patch("/notifications", response_model=NotificationSettingsOut)
async def update_notification_settings(
    body: NotificationSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(NotificationSettings).where(NotificationSettings.user_id == user.id)
    )
    ns = result.scalar_one_or_none()
    if not ns:
        ns = NotificationSettings(user_id=user.id)
        db.add(ns)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(ns, field, value)
    await db.commit()
    await db.refresh(ns)
    return ns
