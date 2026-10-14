"""Inviting people into a company, and removing them on request."""
import random
import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.notification import Notification
from app.models.progress import SavedModule
from app.models.settings import NotificationSettings
from app.models.social import CommentLike, ModuleComment
from app.models.user import Organisation, User
from app.routers.webhooks import deliver_webhook
from app.services.email import send_invite_email

INVITE_TOKEN_TTL = timedelta(days=7)
COLORS = ["#6E2BF0", "#0E9E6E", "#B26A00", "#0B8FB0", "#4338CA"]
REMOVED_NAME = "Removed learner"


async def invite(
    db: AsyncSession, org: Organisation, inviter: User,
    email: str, name: str, role: str | None = None, is_admin: bool = False,
) -> User:
    taken = await db.scalar(select(User.id).where(func.lower(User.email) == email.lower()))
    if taken:
        raise HTTPException(status_code=409, detail="Someone with that email already has an account")
    user = User(
        org_id=org.id, email=email, name=name, initial=name[0].upper(),
        color=random.choice(COLORS), role=role, status="invited", is_admin=is_admin,
        invite_token=secrets.token_urlsafe(32),
        invite_token_expires_at=datetime.utcnow() + INVITE_TOKEN_TTL,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await send_invite_email(user.email, user.name, inviter.name, user.invite_token, org.name)
    await deliver_webhook(db, org.id, "user.invited", {
        "user_id": user.id, "email": user.email, "invited_by": inviter.id,
    })
    return user


async def anonymise(db: AsyncSession, user: User) -> None:
    """GDPR removal. Everything that identifies the person goes: name, email,
    sign-in, comments, notes and settings. Lesson completions, certificates and
    time stay as anonymous records so education totals stay accurate."""
    # Their comments go, with the replies under them (a thread without its
    # question makes no sense), and the likes on all of those
    own = [r for (r,) in (await db.execute(select(ModuleComment.id).where(ModuleComment.user_id == user.id))).all()]
    replies = [r for (r,) in (await db.execute(select(ModuleComment.id).where(ModuleComment.parent_id.in_(own)))).all()]
    gone = own + replies
    await db.execute(delete(CommentLike).where(
        (CommentLike.user_id == user.id) | CommentLike.comment_id.in_(gone)
    ))
    await db.execute(delete(ModuleComment).where(ModuleComment.id.in_(replies)))
    await db.execute(delete(ModuleComment).where(ModuleComment.id.in_(own)))
    await db.execute(delete(Notification).where(Notification.user_id == user.id))
    await db.execute(delete(SavedModule).where(SavedModule.user_id == user.id))
    await db.execute(delete(NotificationSettings).where(NotificationSettings.user_id == user.id))
    await db.execute(delete(Assignment).where(Assignment.user_id == user.id))

    user.name = REMOVED_NAME
    user.initial = "–"
    user.email = f"removed-{user.id}@removed.invalid"
    user.role = None
    user.color = "#C2C4CB"
    user.status = "removed"
    user.is_admin = False
    user.password_hash = None
    user.invite_token = None
    user.invite_token_expires_at = None
    user.department_id = None
    user.last_active_at = None
    await db.commit()
