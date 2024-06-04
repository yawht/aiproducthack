from datetime import datetime
from typing import Optional
from pydantic import UUID4, BaseModel


class GenerationResult(BaseModel):
    uid: UUID4
    started_at: datetime
    finished_at: datetime
    # NOTE either error or image link is defined
    error: Optional[str]
    image_link: Optional[str]


class Generation(BaseModel):
    uid: UUID4
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    metadata: dict

    input_image_link: str
    input_prompt: Optional[str]

    results: list[GenerationResult]
