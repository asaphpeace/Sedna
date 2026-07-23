from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.assignment import Assignment
from app.models.content import Tier
from app.models.notification import Notification
from app.models.org_structure import Department
from app.models.user import User
from app.schemas.org import AssignmentCreate, AssignmentOut, DepartmentIn, DepartmentOut
from app.services.assignment_status import compute_status, send_due_date_reminders
from app.services.deps import admin_user, current_user, manager_or_admin_user, visible_user_ids
from app.services.notifications import create_notification

router = APIRouter(tags=["org"])


# ── Departments (admin only — org structure is an HR/admin concern) ────────
@router.get("/admin/departments", response_model=list[DepartmentOut])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_user),
):
    result = await db.execute(select(Department).where(Department.org_id == admin.org_id))
    depts = result.scalars().all()

    counts_result = await db.execute(
        select(User.department_id, func.count())
        .where(User.org_id == admin.org_id, User.department_id.isnot(None))
        .group_by(User.department_id)
    )
    counts = dict(counts_result.all())

    out = []
    for d in depts:
        out.append(DepartmentOut(
            id=d.id, name=d.name, manager_user_id=d.manager_user_id,
            member_count=counts.get(d.id, 0),
        ))
    return out


@router.post("/admin/departments", response_model=DepartmentOut)
async def create_department(
    body: DepartmentIn,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_user),
):
    dept = Department(org_id=admin.org_id, name=body.name, manager_user_id=body.manager_user_id)
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return DepartmentOut(id=dept.id, name=dept.name, manager_user_id=dept.manager_user_id, member_count=0)


@router.patch("/admin/departments/{dept_id}", response_model=DepartmentOut)
async def update_department(
    dept_id: int,
    body: DepartmentIn,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_user),
):
    result = await db.execute(
        select(Department).where(Department.id == dept_id, Department.org_id == admin.org_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    dept.name = body.name
    dept.manager_user_id = body.manager_user_id
    await db.commit()

    count_result = await db.execute(
        select(func.count()).where(User.department_id == dept_id)
    )
    return DepartmentOut(
        id=dept.id, name=dept.name, manager_user_id=dept.manager_user_id,
        member_count=count_result.scalar() or 0,
    )


@router.delete("/admin/departments/{dept_id}")
async def delete_department(
    dept_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_user),
):
    result = await db.execute(
        select(Department).where(Department.id == dept_id, Department.org_id == admin.org_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    count_result = await db.execute(select(func.count()).where(User.department_id == dept_id))
    if (count_result.scalar() or 0) > 0:
        raise HTTPException(status_code=400, detail="Move members out of this department before deleting it")

    await db.delete(dept)
    await db.commit()
    return {"ok": True}


# ── Assignments ─────────────────────────────────────────────────────────
@router.post("/assignments", response_model=list[AssignmentOut])
async def create_assignments(
    body: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    assigner: User = Depends(manager_or_admin_user),
):
    tier_result = await db.execute(
        select(Tier).where(Tier.id == body.tier_id).options(selectinload(Tier.role))
    )
    tier = tier_result.scalar_one_or_none()
    if not tier:
        raise HTTPException(status_code=404, detail="Tier not found")

    target_ids = set(body.user_ids)
    if body.department_id:
        members_result = await db.execute(
            select(User.id).where(User.department_id == body.department_id, User.org_id == assigner.org_id)
        )
        target_ids.update(row[0] for row in members_result.all())
    if not target_ids:
        raise HTTPException(status_code=400, detail="No recipients specified")

    # A manager may only assign to people they're allowed to see.
    allowed = await visible_user_ids(db, assigner)
    if allowed is not None:
        disallowed = target_ids - set(allowed)
        if disallowed:
            raise HTTPException(status_code=403, detail="Cannot assign training outside your department")

    users_result = await db.execute(select(User).where(User.id.in_(target_ids), User.org_id == assigner.org_id))
    users = users_result.scalars().all()

    created = []
    for u in users:
        existing = await db.execute(
            select(Assignment).where(Assignment.user_id == u.id, Assignment.tier_id == body.tier_id)
        )
        assignment = existing.scalar_one_or_none()
        if assignment:
            assignment.due_date = body.due_date
            assignment.mandatory = body.mandatory
        else:
            assignment = Assignment(
                org_id=assigner.org_id, user_id=u.id, tier_id=body.tier_id,
                due_date=body.due_date, mandatory=body.mandatory, assigned_by_id=assigner.id,
            )
            db.add(assignment)
            await create_notification(
                db, u.id,
                type="training_assigned",
                title=f"New training assigned: {tier.name}",
                body=f"{assigner.name} assigned you {tier.label} — {tier.name}"
                     + (f", due {body.due_date}" if body.due_date else "."),
                icon="ti-clipboard-list", icon_color="#6E2BF0",
                link=f"/paths/{tier.role_id}",
            )
        created.append(assignment)

    await db.commit()

    out = []
    for a in created:
        st = await compute_status(db, a.user_id, a.tier_id, a.due_date)
        u = next(u for u in users if u.id == a.user_id)
        out.append(AssignmentOut(
            id=a.id, user_id=a.user_id, user_name=u.name,
            tier_id=a.tier_id, tier_name=tier.name, role_id=tier.role_id, role_name=tier.role.name,
            due_date=a.due_date, mandatory=a.mandatory, assigned_at=a.assigned_at,
            **st,
        ))
    return out


@router.get("/assignments/me", response_model=list[AssignmentOut])
async def my_assignments(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    result = await db.execute(
        select(Assignment)
        .where(Assignment.user_id == user.id)
        .options(selectinload(Assignment.tier).selectinload(Tier.role))
    )
    assignments = result.scalars().all()

    out = []
    for a in assignments:
        st = await compute_status(db, a.user_id, a.tier_id, a.due_date)
        out.append(AssignmentOut(
            id=a.id, user_id=a.user_id, user_name=user.name,
            tier_id=a.tier_id, tier_name=a.tier.name, role_id=a.tier.role_id, role_name=a.tier.role.name,
            due_date=a.due_date, mandatory=a.mandatory, assigned_at=a.assigned_at,
            **st,
        ))
    out.sort(key=lambda x: (x.status == "complete", x.due_date or date.max))
    return out


@router.get("/assignments", response_model=list[AssignmentOut])
async def list_assignments(
    db: AsyncSession = Depends(get_db),
    viewer: User = Depends(manager_or_admin_user),
):
    allowed = await visible_user_ids(db, viewer)
    query = (
        select(Assignment)
        .where(Assignment.org_id == viewer.org_id)
        .options(selectinload(Assignment.tier).selectinload(Tier.role), selectinload(Assignment.user))
    )
    if allowed is not None:
        if not allowed:
            return []
        query = query.where(Assignment.user_id.in_(allowed))
    result = await db.execute(query)
    assignments = result.scalars().all()

    out = []
    for a in assignments:
        st = await compute_status(db, a.user_id, a.tier_id, a.due_date)
        out.append(AssignmentOut(
            id=a.id, user_id=a.user_id, user_name=a.user.name,
            tier_id=a.tier_id, tier_name=a.tier.name, role_id=a.tier.role_id, role_name=a.tier.role.name,
            due_date=a.due_date, mandatory=a.mandatory, assigned_at=a.assigned_at,
            **st,
        ))
    return out


@router.delete("/assignments/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    assigner: User = Depends(manager_or_admin_user),
):
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment or assignment.org_id != assigner.org_id:
        raise HTTPException(status_code=404, detail="Assignment not found")

    allowed = await visible_user_ids(db, assigner)
    if allowed is not None and assignment.user_id not in allowed:
        raise HTTPException(status_code=403, detail="Cannot remove an assignment outside your department")

    await db.delete(assignment)
    await db.commit()
    return {"ok": True}


@router.post("/admin/assignments/send-reminders")
async def trigger_due_date_reminders(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_user),
):
    """No cron/scheduler exists in this deployment yet, so due-date reminders
    are admin-triggered for now — wire this to a real scheduled job once
    that infra exists."""
    sent = await send_due_date_reminders(db, org_id=admin.org_id)
    return {"reminders_sent": sent}
