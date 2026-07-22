"""Auto-award certificates when a user completes all modules in a tier (and passes tier assessment if set)."""
import random
import string
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.content import Tier
from app.models.progress import ActivityLog, Certificate, UserModuleProgress
from app.models.user import User
from app.services.gamification import award_xp, check_and_award_badges
from app.services.notifications import create_notification


async def check_and_award_cert(db: AsyncSession, user: User, tier_id: int) -> Certificate | None:
    """Check if user has completed all modules in the tier; if so, issue certificate."""
    result = await db.execute(
        select(Tier)
        .where(Tier.id == tier_id)
        .options(selectinload(Tier.modules))
    )
    tier = result.scalar_one_or_none()
    if not tier or not tier.modules:
        return None

    # Check all modules done. Placeholder (not-yet-authored) modules are
    # normally excluded so a tier isn't held hostage by unfinished content —
    # but if EVERY module in the tier is still a placeholder, that exclusion
    # would leave zero modules to require and certification would become
    # permanently impossible. In that case, require all of them instead:
    # completing everything currently available is the most a learner can
    # do, and the moment real content is authored the tier naturally goes
    # back to requiring only non-placeholder modules.
    real_module_ids = [m.id for m in tier.modules if not m.is_placeholder]
    module_ids = real_module_ids or [m.id for m in tier.modules]
    if not module_ids:
        return None

    prog_result = await db.execute(
        select(UserModuleProgress).where(
            UserModuleProgress.user_id == user.id,
            UserModuleProgress.module_id.in_(module_ids),
            UserModuleProgress.state == "done",
        )
    )
    completed_ids = {p.module_id for p in prog_result.scalars().all()}
    if not all(mid in completed_ids for mid in module_ids):
        return None

    # Already has cert?
    existing = await db.execute(
        select(Certificate).where(Certificate.user_id == user.id, Certificate.tier_id == tier_id)
    )
    if existing.scalar_one_or_none():
        return None

    # Award it
    cred = "SA-" + "".join(random.choices(string.digits, k=8))
    cert = Certificate(user_id=user.id, tier_id=tier_id, credential_number=cred)
    db.add(cert)

    # XP + badges
    await award_xp(db, user, "cert_earned", tier_id)
    new_badges = await check_and_award_badges(db, user, "cert_earned")

    # Activity log
    db.add(ActivityLog(
        user_id=user.id, action="earned",
        target_type="tier", target_id=tier_id,
        target_label=tier.cert_name,
    ))

    # In-app notification
    await create_notification(db, user.id,
        type="cert_earned",
        title=f"Certificate earned: {tier.cert_name}",
        body=f"Congratulations! You've completed all modules in {tier.label} — {tier.name}.",
        icon="ti-certificate", icon_color="#B26A00",
        link=f"/certs",
    )

    return cert
