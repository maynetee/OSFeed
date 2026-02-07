from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_default: bool = False
    is_global: bool = False
    parent_id: Optional[UUID] = None
    auto_assign_languages: Optional[List[str]] = None
    auto_assign_keywords: Optional[List[str]] = None
    auto_assign_tags: Optional[List[str]] = None


class CollectionCreate(CollectionBase):
    channel_ids: Optional[List[UUID]] = None


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    channel_ids: Optional[List[UUID]] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_default: Optional[bool] = None
    is_global: Optional[bool] = None
    parent_id: Optional[UUID] = None
    auto_assign_languages: Optional[List[str]] = None
    auto_assign_keywords: Optional[List[str]] = None
    auto_assign_tags: Optional[List[str]] = None


class CollectionResponse(CollectionBase):
    id: UUID
    user_id: Optional[UUID] = None
    channel_ids: List[UUID] = []
    is_curated: bool = False
    region: Optional[str] = None
    topic: Optional[str] = None
    curator: Optional[str] = None
    thumbnail_url: Optional[str] = None
    last_curated_at: Optional[datetime] = None
    curated_channel_usernames: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CuratedCollectionResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    region: Optional[str] = None
    topic: Optional[str] = None
    curator: Optional[str] = None
    channel_count: int = 0
    curated_channel_usernames: List[str] = []
    thumbnail_url: Optional[str] = None
    last_curated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CollectionStatsResponse(BaseModel):
    message_count: int
    message_count_24h: int
    message_count_7d: int
    channel_count: int
    top_channels: List[dict]
    activity_trend: List[dict]
    duplicate_rate: float
    languages: dict
