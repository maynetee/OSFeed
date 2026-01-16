from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID


class ChannelBase(BaseModel):
    username: str


class ChannelCreate(ChannelBase):
    pass


class ChannelResponse(ChannelBase):
    id: UUID
    telegram_id: int
    title: str
    description: Optional[str] = None
    detected_language: Optional[str] = None
    subscriber_count: int
    is_active: bool = True
    fetch_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_fetched_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
