from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class DepartmentIn(BaseModel):
    name: str
    manager_user_id: Optional[int] = None


class DepartmentOut(BaseModel):
    id: int
    name: str
    manager_user_id: Optional[int]
    member_count: int = 0

    model_config = {"from_attributes": True}


class AssignmentCreate(BaseModel):
    user_ids: list[int] = []
    department_id: Optional[int] = None
    tier_id: int
    due_date: Optional[date] = None
    mandatory: bool = True


class AssignmentOut(BaseModel):
    id: int
    user_id: int
    user_name: str
    tier_id: int
    tier_name: str
    role_id: int
    role_name: str
    due_date: Optional[date]
    mandatory: bool
    assigned_at: datetime
    status: str  # not_started | in_progress | complete | overdue
    pct_complete: float
