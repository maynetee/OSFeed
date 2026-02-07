from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DigestPreferenceUpdate(BaseModel):
    enabled: Optional[bool] = None
    frequency: Optional[str] = None
    send_hour: Optional[int] = None
    collection_ids: Optional[List[str]] = None
    max_messages: Optional[int] = None


class DigestPreferenceResponse(BaseModel):
    id: UUID
    user_id: UUID
    enabled: bool
    frequency: str
    send_hour: int
    collection_ids: Optional[List[str]] = None
    max_messages: int
    last_sent_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DigestPreviewRequest(BaseModel):
    collection_ids: Optional[List[str]] = None
    max_messages: Optional[int] = 20
