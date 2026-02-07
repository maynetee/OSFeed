from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SummaryGenerateRequest(BaseModel):
    collection_id: Optional[UUID] = None
    channel_ids: Optional[List[UUID]] = None
    date_range: str = "7d"  # "24h", "7d", "30d"
    max_messages: int = 100


class SummaryResponse(BaseModel):
    id: UUID
    user_id: UUID
    collection_id: Optional[UUID] = None
    channel_ids: List[str] = []
    date_range_start: datetime
    date_range_end: datetime
    summary_text: str
    key_themes: List[str] = []
    notable_events: List[str] = []
    message_count: int = 0
    model_used: Optional[str] = None
    generation_time_seconds: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SummaryListResponse(BaseModel):
    summaries: List[SummaryResponse]
    total: int
