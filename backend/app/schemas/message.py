from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
import json


class MessageResponse(BaseModel):
    id: UUID
    channel_id: UUID
    channel_title: Optional[str] = None
    channel_username: Optional[str] = None
    telegram_message_id: int
    original_text: str
    translated_text: Optional[str] = None
    needs_translation: bool = False
    source_language: Optional[str] = None
    target_language: Optional[str] = "fr"
    translation_priority: Optional[str] = "normal"
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
    duplicate_count: Optional[int] = None
    escalation_score: Optional[float] = None
    escalation_level: Optional[str] = None
    escalation_factors: Optional[List[str]] = None
    has_correlation: bool = False
    pattern_ids: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("media_urls", mode="before")
    @classmethod
    def _parse_media_urls(cls, value):
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else None
            except json.JSONDecodeError:
                return None
        return value


class MessageListResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int
    next_cursor: Optional[str] = None


class SimilarMessagesResponse(BaseModel):
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int
    duplicate_group_id: Optional[UUID] = None
