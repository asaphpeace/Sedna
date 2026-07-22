from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.content import LearningRole, Module, Tier
from app.models.progress import ActivityLog, Certificate, UserModuleProgress
from app.models.user import User
from app.schemas.progress import ModuleProgressOut, RoleProgressOut
from app.services.cert_award import check_and_award_cert
from app.services.deps import current_user
from app.services.email import send_cert_email, send_near_cert_email
from app.services.gamification import award_xp, check_and_award_badges, update_streak
from app.services.notifications import create_notification, notify_near_cert
from app.routers.webhooks import deliver_webhook

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/me", response_model=list[ModuleProgressOut])
async def my_progress(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(UserModuleProgress).where(UserModuleProgress.user_id == user.id)
    )
    return result.scalars().all()


@router.get("/me/paths", response_model=list[RoleProgressOut])
async def my_path_progress(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    roles_result = await db.execute(
        select(LearningRole).options(
            selectinload(LearningRole.tiers).selectinload(Tier.modules)
        )
    )
    roles = roles_result.scalars().all()

    prog_result = await db.execute(
        select(UserModuleProgress).where(UserModuleProgress.user_id == user.id)
    )
    prog_map = {p.module_id: p for p in prog_result.scalars().all()}

    cert_result = await db.execute(
        select(Certificate).where(Certificate.user_id == user.id)
    )
    earned_tier_ids = {c.tier_id for c in cert_result.scalars().all()}

    out = []
    for role in roles:
        total = sum(len(t.modules) for t in role.tiers)
        done = sum(
            1 for t in role.tiers for m in t.modules
            if prog_map.get(m.id) and prog_map[m.id].state == "done"
        )
        pct = int(done / total * 100) if total else 0
        earned = sum(1 for t in role.tiers if t.id in earned_tier_ids)
        out.append(RoleProgressOut(
            role_id=role.id, role_name=role.name,
            pct=pct, done_modules=done, total_modules=total,
            earned_certs=earned, total_certs=len(role.tiers),
        ))
    return out


@router.post("/modules/{module_id}/start")
async def start_module(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    existing = await db.execute(
        select(UserModuleProgress).where(
            UserModuleProgress.user_id == user.id,
            UserModuleProgress.module_id == module_id,
        )
    )
    prog = existing.scalar_one_or_none()
    if not prog:
        prog = UserModuleProgress(
            user_id=user.id, module_id=module_id,
            state="in_progress", pct_complete=0,
            started_at=datetime.utcnow(),
        )
        db.add(prog)
        db.add(ActivityLog(
            user_id=user.id, action="started",
            target_type="module", target_id=module_id,
            target_label=module.title,
        ))
    await db.commit()
    return {"status": "ok"}


@router.post("/modules/{module_id}/complete")
async def complete_module(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    module_result = await db.execute(
        select(Module).where(Module.id == module_id)
    )
    module = module_result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    existing = await db.execute(
        select(UserModuleProgress).where(
            UserModuleProgress.user_id == user.id,
            UserModuleProgress.module_id == module_id,
        )
    )
    prog = existing.scalar_one_or_none()
    now = datetime.utcnow()
    already_done = prog and prog.state == "done"

    if prog:
        prog.state = "done"
        prog.pct_complete = 100
        prog.completed_at = now
    else:
        prog = UserModuleProgress(
            user_id=user.id, module_id=module_id,
            state="done", pct_complete=100,
            started_at=now, completed_at=now,
        )
        db.add(prog)

    xp_awarded = 0
    new_badges: list = []
    cert_earned = False
    cert_name = None
    cert_id = None

    if not already_done:
        # XP + streak + badges
        xp_before = user.xp_total
        await award_xp(db, user, "module_complete", module_id)
        await update_streak(db, user)
        new_badges = await check_and_award_badges(db, user, "module_complete")
        xp_awarded = user.xp_total - xp_before

        db.add(ActivityLog(
            user_id=user.id, action="completed",
            target_type="module", target_id=module_id,
            target_label=module.title,
        ))

        await create_notification(
            db, user.id, type="module_complete",
            title=f"Completed: {module.title}",
            body="Nice work — keep going to unlock your next certificate.",
            icon="ti-circle-check-filled", icon_color="#0E9E6E",
            link=f"/modules/{module_id}",
        )

        # Check cert eligibility for this tier
        tier_result = await db.execute(
            select(Tier).where(Tier.id == module.tier_id).options(selectinload(Tier.modules))
        )
        tier = tier_result.scalar_one_or_none()
        if tier:
            await db.flush()  # ensure prog is visible for cert check
            cert = await check_and_award_cert(db, user, tier.id)

            if cert:
                cert_earned = True
                cert_name = tier.cert_name
                cert_id = cert.id
                await send_cert_email(user.email, user.name, tier.cert_name, cert.credential_number)
            else:
                # Near-cert nudge: count remaining
                all_module_ids = [m.id for m in tier.modules if not m.is_placeholder]
                done_result = await db.execute(
                    select(UserModuleProgress).where(
                        UserModuleProgress.user_id == user.id,
                        UserModuleProgress.module_id.in_(all_module_ids),
                        UserModuleProgress.state == "done",
                    )
                )
                done_count = len(done_result.scalars().all())
                remaining = len(all_module_ids) - done_count
                if 1 <= remaining <= 2:
                    await notify_near_cert(db, user.id, tier.cert_name, remaining, tier.id)
                    await send_near_cert_email(user.email, user.name, tier.cert_name, remaining)

    await db.commit()

    if not already_done:
        await deliver_webhook(db, user.org_id, "module.completed", {
            "user_id": user.id, "module_id": module_id, "module_title": module.title,
        })
        for slug in new_badges:
            await deliver_webhook(db, user.org_id, "badge.earned", {
                "user_id": user.id, "badge_slug": slug,
            })
        if cert_earned:
            await deliver_webhook(db, user.org_id, "cert.earned", {
                "user_id": user.id, "cert_id": cert_id, "cert_name": cert_name,
            })

    return {
        "status": "ok",
        "xp_awarded": xp_awarded,
        "new_badges": [b.slug for b in new_badges],
        "cert_earned": cert_earned,
        "cert_name": cert_name,
        "cert_id": cert_id,
    }
