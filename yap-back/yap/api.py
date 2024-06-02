from datetime import datetime
from typing import Optional
from pydantic import UUID4, BaseModel


class Generation(BaseModel):
    uid: UUID4
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    finished_at: Optional[datetime]
    metadata: dict
