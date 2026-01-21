from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID


class FetchJobStatus(BaseModel):
    id: UUID
    channel_id: UUID
    days: int
    status: str
    stage: Optional[str] = None
    total_messages: Optional[int] = None
    new_messages: Optional[int] = None
    processed_messages: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
