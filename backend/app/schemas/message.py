from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


class MessageResponse(BaseModel):
    id: UUID
    channel_id: UUID
    telegram_message_id: int
    original_text: str
    translated_text: Optional[str] = None
    source_language: Optional[str] = None
    target_language: Optional[str] = "fr"
    media_type: Optional[str] = None
    media_urls: Optional[List[str]] = None
    is_duplicate: bool = False
    originality_score: Optional[int] = 100
    duplicate_group_id: Optional[UUID] = None
    embedding_id: Optional[str] = None
    entities: Optional[Dict[str, List[str]]] = None
    published_at: datetime
    fetched_at: datetime
    translated_at: Optional[datetime] = None
    similarity_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int
