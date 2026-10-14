"""Learning impact dashboard: Reach and Health across every company.

Only Sedna admins can see it. The smallest unit of value is a completed
lesson, so the headline numbers count lessons and the people who completed
them; certificates and time spent sit beside them.
"""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from statistics import median
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.content import LearningRole, Module, Tier
from app.models.progress import Certificate, LearningTime, UserModuleProgress
from app.models.user import Organisation, User
from app.services.deps import sedna_admin_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

Period = Literal["month", "quarter", "last_quarter", "12m"]
PERIOD_LABELS = {
    "month": "This month",
    "quarter": "This quarter",
    "last_quarter": "Last quarter",
    "12m": "Last 12 months",
}
IDLE_DAYS = 14


def _period_bounds(period: str, now: datetime) -> tuple[datetime, datetime]:
    today = datetime(now.year, now.month, now.day)
    if period == "month":
        return datetime(now.year, now.month, 1), today + timedelta(days=1)
    q_start_month = 3 * ((now.month - 1) // 3) + 1
    q_start = datetime(now.year, q_start_month, 1)
    if period == "quarter":
        return q_start, today + timedelta(days=1)
    if period == "last_quarter":
        prev_month = q_start_month - 3
        year = now.year if prev_month > 0 else now.year - 1
        return datetime(year, (prev_month - 1) % 12 + 1, 1), q_start
    return today + timedelta(days=1) - timedelta(days=365), today + timedelta(days=1)


def _months_back(end: datetime, n: int) -> list[str]:
    y, m = end.year, end.month
    if end.day == 1 and end.hour == 0:  # an exclusive bound on the 1st belongs to the month before
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return out[::-1]


def _in(ts: Optional[datetime], start: datetime, end: datetime) -> bool:
    return ts is not None and start <= ts < end


def _day_in(d: date, start: datetime, end: datetime) -> bool:
    return start.date() <= d < end.date()


def _delta(cur: float, prev: float) -> dict:
    return {"value": cur, "previous": prev}


@router.get("/impact")
async def learning_impact(
    period: Period = "last_quarter",
    audience: Literal["all", "staff", "customer"] = "all",
    org_id: Optional[int] = Query(None),
    product: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(sedna_admin_user),
):
    now = datetime.utcnow()
    start, end = _period_bounds(period, now)
    prev_start, prev_end = start - (end - start), start

    # ── Who is in scope ─────────────────────────────────────
    orgs = (await db.execute(select(Organisation).order_by(Organisation.name))).scalars().all()
    org_by_id = {o.id: o for o in orgs}
    scoped_orgs = [
        o for o in orgs
        if (audience == "all" or (o.kind == "sedna") == (audience == "staff"))
        and (org_id is None or o.id == org_id)
    ]
    scoped_org_ids = {o.id for o in scoped_orgs}
    users = (await db.execute(
        select(User).where(User.org_id.in_(scoped_org_ids), User.status == "active")
    )).scalars().all() if scoped_org_ids else []
    user_by_id = {u.id: u for u in users}
    user_ids = list(user_by_id)

    def is_staff(uid: int) -> bool:
        org = org_by_id.get(user_by_id[uid].org_id)
        return bool(org and org.kind == "sedna")

    # ── Which lessons count: real ones, in paths of the chosen product ──
    rows = (await db.execute(
        select(Module, Tier, LearningRole)
        .join(Tier, Module.tier_id == Tier.id)
        .join(LearningRole, Tier.role_id == LearningRole.id)
        .where(Module.is_placeholder == False)
    )).all()
    rows = [r for r in rows if product is None or product in (r.LearningRole.products or [])]
    module_by_id = {r.Module.id: r.Module for r in rows}
    path_of = {r.Module.id: r.LearningRole for r in rows}
    path_lessons: dict[int, list[tuple]] = defaultdict(list)
    for r in rows:
        path_lessons[r.LearningRole.id].append((r.Tier.sort_order, r.Module.sort_order, r.Module.id))
    path_order = {pid: [mid for *_, mid in sorted(ls)] for pid, ls in path_lessons.items()}
    paths = {r.LearningRole.id: r.LearningRole for r in rows}
    tier_ids = {r.Tier.id for r in rows}

    progress = (await db.execute(
        select(UserModuleProgress).where(
            UserModuleProgress.user_id.in_(user_ids),
            UserModuleProgress.module_id.in_(module_by_id),
        )
    )).scalars().all() if user_ids and module_by_id else []
    done = [p for p in progress if p.state == "done" and p.completed_at]

    certs = (await db.execute(
        select(Certificate).where(Certificate.user_id.in_(user_ids), Certificate.tier_id.in_(tier_ids))
    )).scalars().all() if user_ids and tier_ids else []

    times = (await db.execute(
        select(LearningTime).where(
            LearningTime.user_id.in_(user_ids), LearningTime.module_id.in_(module_by_id),
        )
    )).scalars().all() if user_ids and module_by_id else []

    # ── Reach ───────────────────────────────────────────────
    def reach(s: datetime, e: datetime) -> dict:
        completed = [p for p in done if _in(p.completed_at, s, e)]
        active = {p.user_id for p in progress if _in(p.started_at, s, e) or _in(p.completed_at, s, e)}
        active |= {t.user_id for t in times if _day_in(t.day, s, e)}
        return {
            "people": len({p.user_id for p in completed}),
            "lessons": len(completed),
            "certificates": sum(1 for c in certs if _in(c.issued_at, s, e)),
            "active": len(active),
            "tracked_minutes": round(sum(t.seconds for t in times if _day_in(t.day, s, e)) / 60),
            "estimated_minutes": sum(module_by_id[p.module_id].duration_mins or 0 for p in completed),
        }

    cur, prev = reach(start, end), reach(prev_start, prev_end)
    headline = {k: _delta(cur[k], prev[k]) for k in cur}

    months = _months_back(end, 6)
    trend = {m: {"month": m, "staff": 0, "customer": 0} for m in months}
    for p in done:
        key = p.completed_at.strftime("%Y-%m")
        if key in trend:
            trend[key]["staff" if is_staff(p.user_id) else "customer"] += 1

    companies = []
    for o in scoped_orgs:
        members = {u.id for u in users if u.org_id == o.id}
        if not members:
            continue
        active = {p.user_id for p in progress if p.user_id in members and (_in(p.started_at, start, end) or _in(p.completed_at, start, end))}
        active |= {t.user_id for t in times if t.user_id in members and _day_in(t.day, start, end)}
        companies.append({
            "org_id": o.id,
            "name": o.name,
            "kind": o.kind,
            "users": len(members),
            "active": len(active),
            "coverage": round(len(active) / len(members) * 100),
            "lessons": sum(1 for p in done if p.user_id in members and _in(p.completed_at, start, end)),
            "certificates": sum(1 for c in certs if c.user_id in members and _in(c.issued_at, start, end)),
            "tracked_minutes": round(sum(t.seconds for t in times if t.user_id in members and _day_in(t.day, start, end)) / 60),
        })
    companies.sort(key=lambda c: (-c["lessons"], c["name"]))

    # ── Health (all time, for the people in scope) ──────────
    by_user_path: dict[tuple[int, int], dict[int, UserModuleProgress]] = defaultdict(dict)
    for p in progress:
        by_user_path[(p.user_id, path_of[p.module_id].id)][p.module_id] = p
    minutes_by_path: Counter = Counter()
    for t in times:
        minutes_by_path[path_of[t.module_id].id] += t.seconds / 60

    path_stats = []
    unfinished: dict[int, list[int]] = defaultdict(list)  # user → paths they started but didn't finish
    for pid, lessons in path_order.items():
        learners = [(uid, mods) for (uid, p2), mods in by_user_path.items() if p2 == pid]
        if not learners:
            continue
        finished, days, drop = 0, [], Counter()
        for uid, mods in learners:
            if all(mods.get(m) and mods[m].state == "done" for m in lessons):
                finished += 1
                starts = [x.started_at for x in mods.values() if x.started_at]
                ends = [x.completed_at for x in mods.values() if x.completed_at]
                if starts and ends:
                    days.append((max(ends) - min(starts)).total_seconds() / 86400)
            else:
                unfinished[uid].append(pid)
                first_open = next(m for m in lessons if not (mods.get(m) and mods[m].state == "done"))
                drop[first_open] += 1
        drop_id, drop_count = drop.most_common(1)[0] if drop else (None, 0)
        path_stats.append({
            "path_id": pid,
            "name": paths[pid].name,
            "audience": paths[pid].audience,
            "lessons": len(lessons),
            "started": len(learners),
            "finished": finished,
            "completion_rate": round(finished / len(learners) * 100),
            "median_days": round(median(days), 1) if days else None,
            "tracked_minutes": round(minutes_by_path[pid]),
            "dropoff": {"module_id": drop_id, "title": module_by_id[drop_id].title, "learners": drop_count} if drop_id else None,
        })
    path_stats.sort(key=lambda p: (-p["started"], p["name"]))

    last_seen: dict[int, datetime] = {}
    for p in progress:
        for ts in (p.started_at, p.completed_at):
            if ts and ts > last_seen.get(p.user_id, datetime.min):
                last_seen[p.user_id] = ts
    for t in times:
        ts = datetime(t.day.year, t.day.month, t.day.day)
        if ts > last_seen.get(t.user_id, datetime.min):
            last_seen[t.user_id] = ts
    idle = []
    for uid, pids in unfinished.items():
        seen = last_seen.get(uid)
        if seen and (now - seen).days >= IDLE_DAYS:
            u = user_by_id[uid]
            idle.append({
                "user_id": uid,
                "name": u.name,
                "company": org_by_id[u.org_id].name,
                "paths": [paths[p].name for p in pids],
                "days_idle": (now - seen).days,
            })
    idle.sort(key=lambda r: -r["days_idle"])

    return {
        "period": {
            "key": period, "label": PERIOD_LABELS[period],
            "start": start.date().isoformat(), "end": (end - timedelta(days=1)).date().isoformat(),
            "previous_start": prev_start.date().isoformat(), "previous_end": (prev_end - timedelta(days=1)).date().isoformat(),
        },
        "headline": headline,
        "trend": list(trend.values()),
        "companies": companies,
        "paths": path_stats,
        "attention": {
            "paths": [p for p in path_stats if p["started"] >= 3 and p["completion_rate"] < 20],
            "idle_learners": idle[:25],
            "idle_days": IDLE_DAYS,
        },
        "filters": {"companies": [{"id": o.id, "name": o.name, "kind": o.kind} for o in orgs]},
    }
