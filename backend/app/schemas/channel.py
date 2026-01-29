from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from app.schemas.fetch_job import FetchJobStatus


class ChannelBase(BaseModel):
    username: str


class ChannelCreate(ChannelBase):
    pass


class ChannelResponse(ChannelBase):
    id: UUID
    telegram_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    detected_language: Optional[str] = None
    subscriber_count: int
    is_active: bool = True
    tags: Optional[list[str]] = None
    fetch_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_fetched_at: Optional[datetime] = None
    fetch_job: Optional[FetchJobStatus] = None

    model_config = ConfigDict(from_attributes=True)


class BulkChannelCreate(BaseModel):
    usernames: List[str]


class BulkChannelFailure(BaseModel):
    username: str
    error: str


class BulkChannelResponse(BaseModel):
    succeeded: List[ChannelResponse]
    failed: List[BulkChannelFailure]
    total: int
    success_count: int
    failure_count: int
