from typing import Optional

from pydantic import BaseModel


class ModuleOut(BaseModel):
    id: int
    title: str
    module_type: str
    duration_mins: int
    product: str
    is_placeholder: bool
    sort_order: int
    description: str
    learn_items: list[str]
    tier_id: int
    role_id: Optional[int] = None
    video_url: Optional[str] = None
    rich_content: Optional[str] = None
    transcript: Optional[str] = None
    audio_url: Optional[str] = None

    model_config = {"from_attributes": True}


class TierOut(BaseModel):
    id: int
    label: str
    name: str
    cert_name: str
    sort_order: int
    modules: list[ModuleOut]

    model_config = {"from_attributes": True}


class LearningRoleOut(BaseModel):
    id: int
    name: str
    description: str
    icon: str
    color: str
    audience: str
    products: list[str]
    sort_order: int
    tiers: list[TierOut]

    model_config = {"from_attributes": True}


class LearningRoleSummary(BaseModel):
    id: int
    name: str
    description: str
    icon: str
    color: str
    audience: str
    products: list[str]
    mod_count: int
    tier_count: int

    model_config = {"from_attributes": True}
