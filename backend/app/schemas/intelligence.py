from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID

class EntityRef(BaseModel):
    id: UUID
    name: str
    type: str
    frequency: int

class ClusterBase(BaseModel):
    id: UUID
    title: Optional[str]
    summary: Optional[str]
    message_count: int
    sentiment_score: Optional[float]
    urgency_score: Optional[int]
    updated_at: datetime
    first_message_at: Optional[datetime]
    primary_source_channel_id: Optional[UUID]

class ClusterList(ClusterBase):
    pass

class ClusterDetail(ClusterBase):
    messages_preview: List[dict]  # Simplified message objects
    entities: List[EntityRef]
    timeline: List[dict] # {time, count}

class IntelligenceDashboard(BaseModel):
    hot_topics: List[ClusterList]
    top_entities: Dict[str, List[EntityRef]]
    global_tension: int
