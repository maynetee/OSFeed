from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID


class SummaryResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    digest_type: str = "daily"
    title: Optional[str] = None
    content: str
    content_html: Optional[str] = None
    entities: Optional[Dict[str, List[str]]] = None
    message_count: int = 0
    channels_covered: int = 0
    duplicates_filtered: int = 0
    period_start: datetime
    period_end: datetime
    filters: Optional[Dict[str, List[str]]] = None
    generated_at: datetime

    class Config:
        from_attributes = True


class SummaryGenerateRequest(BaseModel):
    digest_type: str = "daily"
    filters: Optional[Dict[str, List[str]]] = None
