from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class AlertBase(BaseModel):
    name: str
    collection_id: UUID
    keywords: Optional[List[str]] = None
    entities: Optional[List[str]] = None
    match_mode: str = "any"
    min_threshold: int = 1
    frequency: str = "daily"
    notification_channels: Optional[List[str]] = None
    is_active: bool = True


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    name: Optional[str] = None
    collection_id: Optional[UUID] = None
    keywords: Optional[List[str]] = None
    entities: Optional[List[str]] = None
    match_mode: Optional[str] = None
    min_threshold: Optional[int] = None
    frequency: Optional[str] = None
    notification_channels: Optional[List[str]] = None
    is_active: Optional[bool] = None


class AlertResponse(AlertBase):
    id: UUID
    user_id: UUID
    last_triggered_at: Optional[datetime] = None
    last_evaluated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AlertTriggerResponse(BaseModel):
    id: UUID
    alert_id: UUID
    triggered_at: datetime
    message_ids: List[str]
    summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
