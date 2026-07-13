from datetime import datetime

from pydantic import BaseModel


class ReleaseOut(BaseModel):
    id: int
    product: str
    tag: str
    title: str
    description: str
    published_at: datetime
    module_count: int

    model_config = {"from_attributes": True}
