from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    initial: str
    color: str
    role: Optional[str]
    status: str
    is_admin: bool
    org_id: int
    last_active_at: Optional[datetime]
    department_id: Optional[int] = None
    is_manager: bool = False

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    color: Optional[str] = None
    is_admin: Optional[bool] = None
    department_id: Optional[int] = None


class UserInvite(BaseModel):
    email: EmailStr
    name: str
    role: Optional[str] = None
