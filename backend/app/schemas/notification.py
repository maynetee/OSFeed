from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    title: str
    body: Optional[str] = None
    link: Optional[str] = None
    is_read: bool
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    unread_count: int
    total: int
