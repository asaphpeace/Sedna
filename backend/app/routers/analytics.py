from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.content import LearningRole, Module, Tier
from app.models.progress import ActivityLog, Certificate, UserModuleProgress
from app.models.user import User
from app.services.deps import admin_user, current_user
from app.services.gamification import xp_to_level

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/me")
async def my_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    prog_result = await db.execute(
        select(UserModuleProgress).where(
            UserModuleProgress.user_id == user.id,
            UserModuleProgress.state == "done",
        )
    )
    done = prog_result.scalars().all()

    cert_result = await db.execute(
        select(Certificate).where(Certificate.user_id == user.id)
    )
    certs = cert_result.scalars().all()

    # Activity last 30 days
    since = datetime.utcnow() - timedelta(days=30)
    activity_result = await db.execute(
        select(ActivityLog).where(
            ActivityLog.user_id == user.id,
            ActivityLog.created_at >= since,
        ).order_by(ActivityLog.created_at)
    )
    activities = activity_result.scalars().all()

    # Group by date for heatmap
    heatmap: dict[str, int] = {}
    for a in activities:
        day = a.created_at.strftime("%Y-%m-%d")
        heatmap[day] = heatmap.get(day, 0) + 1

    level_info = xp_to_level(user.xp_total)

    return {
        "modules_completed": len(done),
        "certs_earned": len(certs),
        "xp_total": user.xp_total,
        "level": level_info["level"],
        "level_name": level_info["name"],
        "activity_heatmap": heatmap,
    }


@router.get("/org")
async def org_analytics(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_user),
):
    # All learners in org
    learner_result = await db.execute(
        select(User).where(User.org_id == admin.org_id, User.status == "active", User.is_admin == False)
    )
    learners = learner_result.scalars().all()
    learner_ids = [u.id for u in learners]

    # Module completions per learner
    prog_result = await db.execute(
        select(UserModuleProgress).where(
            UserModuleProgress.user_id.in_(learner_ids),
            UserModuleProgress.state == "done",
        )
    )
    all_progress = prog_result.scalars().all()
    completions_by_user: dict[int, int] = {}
    for p in all_progress:
        completions_by_user[p.user_id] = completions_by_user.get(p.user_id, 0) + 1

    # Certs
    cert_result = await db.execute(
        select(Certificate).where(Certificate.user_id.in_(learner_ids))
    )
    certs_by_user: dict[int, int] = {}
    for c in cert_result.scalars().all():
        certs_by_user[c.user_id] = certs_by_user.get(c.user_id, 0) + 1

    # Total modules available
    total_modules_result = await db.execute(select(func.count(Module.id)))
    total_modules = total_modules_result.scalar() or 1

    # Engagement risk: learners with 0 activity in 14 days
    since = datetime.utcnow() - timedelta(days=14)
    recent_activity_result = await db.execute(
        select(ActivityLog.user_id).where(
            ActivityLog.user_id.in_(learner_ids),
            ActivityLog.created_at >= since,
        ).distinct()
    )
    active_ids = {row[0] for row in recent_activity_result.all()}
    at_risk = [u.id for u in learners if u.id not in active_ids]

    # Module completion rates
    module_result = await db.execute(
        select(Module).where(Module.is_placeholder == False)
    )
    modules = module_result.scalars().all()

    module_stats = []
    for m in modules:
        done_count = sum(1 for p in all_progress if p.module_id == m.id)
        module_stats.append({
            "module_id": m.id,
            "title": m.title,
            "completion_rate": round(done_count / len(learner_ids) * 100) if learner_ids else 0,
        })
    module_stats.sort(key=lambda x: x["completion_rate"], reverse=True)

    return {
        "total_learners": len(learners),
        "active_last_14_days": len(active_ids),
        "at_risk_count": len(at_risk),
        "at_risk_user_ids": at_risk,
        "total_completions": len(all_progress),
        "avg_completions_per_learner": round(len(all_progress) / len(learners), 1) if learners else 0,
        "total_certs": sum(certs_by_user.values()),
        "org_completion_rate": round(len(all_progress) / (total_modules * max(len(learners), 1)) * 100),
        "top_modules": module_stats[:10],
        "bottom_modules": module_stats[-10:],
        "learners": [
            {
                "user_id": u.id,
                "name": u.name,
                "email": u.email,
                "xp_total": u.xp_total,
                "modules_done": completions_by_user.get(u.id, 0),
                "certs_earned": certs_by_user.get(u.id, 0),
                "at_risk": u.id in at_risk,
                "completion_rate": round(completions_by_user.get(u.id, 0) / total_modules * 100),
            }
            for u in learners
        ],
    }
