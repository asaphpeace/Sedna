from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ModuleProgressOut(BaseModel):
    module_id: int
    state: str
    pct_complete: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class CertificateOut(BaseModel):
    id: int
    tier_id: int
    tier_name: str
    cert_name: str
    credential_number: str
    issued_at: datetime
    recipient: str

    model_config = {"from_attributes": True}


class SavedModuleOut(BaseModel):
    module_id: int
    title: str
    module_type: str
    duration_mins: int
    product: str
    tier_name: str
    role_name: str
    saved_at: datetime

    model_config = {"from_attributes": True}


class ActivityOut(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_initial: str
    user_color: str
    action: str
    target_type: str
    target_label: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleProgressOut(BaseModel):
    role_id: int
    role_name: str
    pct: int
    done_modules: int
    total_modules: int
    earned_certs: int
    total_certs: int
