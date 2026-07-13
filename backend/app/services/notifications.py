"""Create in-app notifications and (optionally) send emails."""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def create_notification(
    db: AsyncSession,
    user_id: int,
    type: str,
    title: str,
    body: str = "",
    icon: str = "ti-bell",
    icon_color: str = "#6E2BF0",
    link: Optional[str] = None,
) -> Notification:
    n = Notification(
        user_id=user_id, type=type, title=title, body=body,
        icon=icon, icon_color=icon_color, link=link,
    )
    db.add(n)
    return n


async def notify_badge(db: AsyncSession, user_id: int, badge_name: str, badge_icon: str, badge_color: str):
    await create_notification(db, user_id,
        type="badge_earned",
        title=f"Badge unlocked: {badge_name}",
        body="Keep going — more badges await.",
        icon=badge_icon, icon_color=badge_color,
        link="/progress",
    )


async def notify_near_cert(db: AsyncSession, user_id: int, cert_name: str, modules_left: int, tier_id: int):
    await create_notification(db, user_id,
        type="near_cert",
        title=f"You're {modules_left} module{'s' if modules_left > 1 else ''} from your certificate",
        body=f"Complete the remaining modules to earn {cert_name}.",
        icon="ti-certificate", icon_color="#B26A00",
        link=f"/paths",
    )
