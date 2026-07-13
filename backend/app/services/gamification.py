"""Award XP, badges, and update streaks after learning events."""
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import Badge, UserBadge, UserStreak, UserXP
from app.models.progress import Certificate, UserModuleProgress
from app.models.user import User

XP_VALUES = {
    "module_complete": 10,
    "quiz_first_pass": 20,
    "cert_earned": 100,
    "streak_day": 5,
    "badge_earned": 15,
}

LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2200, 3000, 4000, 5500]
LEVEL_NAMES = ["Newcomer", "Learner", "Practitioner", "Specialist",
               "Expert", "Senior Expert", "Lead", "Master", "Grand Master", "Legend"]


def xp_to_level(xp: int) -> dict:
    level = 0
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if xp >= threshold:
            level = i
    next_threshold = LEVEL_THRESHOLDS[level + 1] if level + 1 < len(LEVEL_THRESHOLDS) else None
    if next_threshold:
        span = next_threshold - LEVEL_THRESHOLDS[level]
        pct = int((xp - LEVEL_THRESHOLDS[level]) / span * 100) if span > 0 else 100
    else:
        pct = 100
    return {
        "level": level + 1,
        "name": LEVEL_NAMES[level],
        "xp": xp,
        "next_level_xp": next_threshold,
        "pct_to_next": pct,
    }


async def award_xp(db: AsyncSession, user: User, source: str, source_id: Optional[int] = None) -> int:
    xp = XP_VALUES.get(source, 0)
    if xp <= 0:
        return 0
    db.add(UserXP(user_id=user.id, source=source, source_id=source_id, xp=xp))
    user.xp_total = (user.xp_total or 0) + xp
    return xp


async def update_streak(db: AsyncSession, user: User) -> dict:
    result = await db.execute(select(UserStreak).where(UserStreak.user_id == user.id))
    streak = result.scalar_one_or_none()
    today = date.today()

    if not streak:
        streak = UserStreak(user_id=user.id, current_streak=1, longest_streak=1, last_activity_date=today)
        db.add(streak)
        await award_xp(db, user, "streak_day")
        return {"current": 1, "longest": 1, "new_day": True}

    if streak.last_activity_date == today:
        return {"current": streak.current_streak, "longest": streak.longest_streak, "new_day": False}

    yesterday = date.fromordinal(today.toordinal() - 1)
    if streak.last_activity_date == yesterday:
        streak.current_streak += 1
    else:
        streak.current_streak = 1

    streak.longest_streak = max(streak.longest_streak, streak.current_streak)
    streak.last_activity_date = today
    await award_xp(db, user, "streak_day")
    return {"current": streak.current_streak, "longest": streak.longest_streak, "new_day": True}


async def check_and_award_badges(db: AsyncSession, user: User, event: str, **kwargs) -> list[str]:
    """Check badge eligibility after an event and award any newly earned badges."""
    result = await db.execute(select(UserBadge.badge_id).where(UserBadge.user_id == user.id))
    earned_ids = {r[0] for r in result.all()}

    badges_result = await db.execute(select(Badge))
    all_badges = {b.slug: b for b in badges_result.scalars().all()}

    newly_earned = []

    async def award(slug: str):
        badge = all_badges.get(slug)
        if badge and badge.id not in earned_ids:
            db.add(UserBadge(user_id=user.id, badge_id=badge.id))
            await award_xp(db, user, "badge_earned", badge.id)
            newly_earned.append(slug)

    # Module-based badges
    if event == "module_complete":
        mod_count_result = await db.execute(
            select(func.count()).where(UserModuleProgress.user_id == user.id, UserModuleProgress.state == "done")
        )
        mod_count = mod_count_result.scalar_one()
        if mod_count >= 1:
            await award("first_module")
        if mod_count >= 10:
            await award("ten_modules")
        if mod_count >= 50:
            await award("fifty_modules")

    # Streak badges
    if event == "streak":
        streak_days = kwargs.get("streak_days", 0)
        if streak_days >= 7:
            await award("streak_7")
        if streak_days >= 30:
            await award("streak_30")

    # Cert badges
    if event == "cert_earned":
        cert_count_result = await db.execute(
            select(func.count()).where(Certificate.user_id == user.id)
        )
        cert_count = cert_count_result.scalar_one()
        if cert_count >= 1:
            await award("first_cert")
        if cert_count >= 5:
            await award("five_certs")

    # Explorer: modules from all 3 products
    if event == "module_complete":
        from app.models.content import Module
        products_result = await db.execute(
            select(Module.product).distinct()
            .join(UserModuleProgress, UserModuleProgress.module_id == Module.id)
            .where(UserModuleProgress.user_id == user.id, UserModuleProgress.state == "done")
        )
        products = {r[0] for r in products_result.all()}
        if {"vms", "stream", "cross"}.issubset(products):
            await award("explorer")

    return newly_earned
