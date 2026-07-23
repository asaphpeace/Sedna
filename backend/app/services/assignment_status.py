"""Compute an assignment's completion status against a user's module progress —
mirrors the module-set logic in cert_award.py so "assigned" and "certified"
never disagree about what counts as done."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment
from app.models.content import Tier
from app.models.notification import Notification
from app.models.progress import UserModuleProgress
from app.services.notifications import create_notification


async def compute_status(db: AsyncSession, user_id: int, tier_id: int, due_date: date | None) -> dict:
    result = await db.execute(
        select(Tier).where(Tier.id == tier_id).options(selectinload(Tier.modules))
    )
    tier = result.scalar_one_or_none()
    if not tier or not tier.modules:
        return {"status": "not_started", "pct_complete": 0.0}

    real_module_ids = [m.id for m in tier.modules if not m.is_placeholder]
    module_ids = real_module_ids or [m.id for m in tier.modules]
    if not module_ids:
        return {"status": "not_started", "pct_complete": 0.0}

    prog_result = await db.execute(
        select(UserModuleProgress).where(
            UserModuleProgress.user_id == user_id,
            UserModuleProgress.module_id.in_(module_ids),
        )
    )
    progress = prog_result.scalars().all()
    done_count = sum(1 for p in progress if p.state == "done")
    pct = round((done_count / len(module_ids)) * 100, 1)

    if done_count == len(module_ids):
        status = "complete"
    elif due_date and date.today() > due_date:
        status = "overdue"
    elif progress:
        status = "in_progress"
    else:
        status = "not_started"

    return {"status": status, "pct_complete": pct}


# Buckets checked in order — a learner gets at most one reminder per bucket
# per assignment, deduped via a hidden marker tucked into the notification
# body (no schema changes needed to track "already sent").
REMINDER_BUCKETS = [(7, "7d"), (1, "1d"), (0, "overdue")]


async def send_due_date_reminders(db: AsyncSession, org_id: int | None = None) -> int:
    """Notify learners about mandatory assignments due soon or overdue.

    No cron/scheduler exists in this deployment yet — this is meant to be
    called from an admin-triggered endpoint for now, and wired to a real
    scheduled job (cron, Celery beat, etc.) once that infra exists.
    """
    query = select(Assignment).where(Assignment.mandatory.is_(True), Assignment.due_date.isnot(None))
    if org_id is not None:
        query = query.where(Assignment.org_id == org_id)
    query = query.options(selectinload(Assignment.tier).selectinload(Tier.role), selectinload(Assignment.user))
    result = await db.execute(query)
    assignments = result.scalars().all()

    today = date.today()
    sent = 0
    for a in assignments:
        status = await compute_status(db, a.user_id, a.tier_id, a.due_date)
        if status["status"] == "complete":
            continue

        days_left = (a.due_date - today).days
        bucket = None
        for threshold, name in REMINDER_BUCKETS:
            if (name == "overdue" and days_left < 0) or (name != "overdue" and days_left == threshold):
                bucket = name
                break
        if not bucket:
            continue

        # The bucket is encoded into `type` (not shown in the UI) purely for
        # dedup — it's the cheapest way to track "already sent" without a
        # new column or table.
        notif_type = f"assignment_reminder:{a.id}:{bucket}"
        existing = await db.execute(
            select(Notification).where(Notification.user_id == a.user_id, Notification.type == notif_type)
        )
        if existing.scalars().first():
            continue

        if bucket == "overdue":
            title = f"Overdue: {a.tier.name}"
            body = f"This training was due {a.due_date} — please complete it as soon as possible."
        else:
            title = f"Training due soon: {a.tier.name}"
            body = f"{a.tier.role.name} — {a.tier.name} is due {a.due_date}."

        await create_notification(
            db, a.user_id,
            type=notif_type,
            title=title,
            body=body,
            icon="ti-alert-circle" if bucket == "overdue" else "ti-clock",
            icon_color="#C0392B" if bucket == "overdue" else "#B26A00",
            link=f"/paths/{a.tier.role_id}",
        )
        sent += 1

    await db.commit()
    return sent
