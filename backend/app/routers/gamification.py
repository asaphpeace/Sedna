from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.gamification import Badge, UserBadge, UserStreak, UserXP
from app.models.user import User
from app.services.deps import current_user
from app.services.gamification import xp_to_level

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/me")
async def my_gamification(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    # Streak
    streak_result = await db.execute(
        select(UserStreak).where(UserStreak.user_id == user.id)
    )
    streak = streak_result.scalar_one_or_none()

    # Badges
    badge_result = await db.execute(
        select(UserBadge)
        .where(UserBadge.user_id == user.id)
        .options(selectinload(UserBadge.badge))
        .order_by(UserBadge.earned_at.desc())
    )
    user_badges = badge_result.scalars().all()

    level_info = xp_to_level(user.xp_total)

    return {
        "xp_total": user.xp_total,
        "level": level_info["level"],
        "level_name": level_info["name"],
        "pct_to_next": level_info["pct_to_next"],
        "xp_to_next": level_info["next_level_xp"],
        "streak": {
            "current": streak.current_streak if streak else 0,
            "longest": streak.longest_streak if streak else 0,
            "last_activity": streak.last_activity_date if streak else None,
        },
        "badges": [
            {
                "slug": ub.badge.slug,
                "name": ub.badge.name,
                "description": ub.badge.description,
                "icon": ub.badge.icon,
                "color": ub.badge.color,
                "bg_color": ub.badge.bg_color,
                "earned_at": ub.earned_at,
            }
            for ub in user_badges
        ],
    }


@router.get("/leaderboard")
async def leaderboard(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(User)
        .where(User.org_id == user.org_id, User.status == "active")
        .order_by(User.xp_total.desc(), User.id)
        .limit(limit)
    )
    users = result.scalars().all()

    board = []
    for rank, u in enumerate(users, 1):
        lvl = xp_to_level(u.xp_total)
        board.append({
            "rank": rank,
            "user_id": u.id,
            "name": u.name,
            "avatar_initials": "".join(p[0].upper() for p in u.name.split()[:2]),
            "xp_total": u.xp_total,
            "level": lvl["level"],
            "level_name": lvl["name"],
            "is_me": u.id == user.id,
        })
    return board


@router.get("/badges")
async def all_badges(db: AsyncSession = Depends(get_db), _: User = Depends(current_user)):
    result = await db.execute(select(Badge).order_by(Badge.id))
    badges = result.scalars().all()
    return [
        {
            "slug": b.slug,
            "name": b.name,
            "description": b.description,
            "icon": b.icon,
            "color": b.color,
            "bg_color": b.bg_color,
        }
        for b in badges
    ]
