"""Pydantic schemas for intelligence analysis features."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# === Escalation Scoring ===

class EscalationScoreResponse(BaseModel):
    id: UUID
    message_id: UUID
    score: float
    level: str
    factors: List[str] = []
    computed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EscalationTrendPoint(BaseModel):
    date: str
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    avg_score: float = 0.0


class EscalationTrendResponse(BaseModel):
    period: str
    trend: List[EscalationTrendPoint] = []
    total_high: int = 0
    total_medium: int = 0
    total_low: int = 0


# === Cross-Source Correlation ===

class CorrelationResponse(BaseModel):
    id: UUID
    duplicate_group_id: UUID
    analysis_text: Optional[str] = None
    consistent_facts: List[str] = []
    unique_details: List[str] = []
    contradictions: List[str] = []
    source_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CorrelationListResponse(BaseModel):
    correlations: List[CorrelationResponse] = []
    total: int = 0


# === Pattern Detection ===

class DetectedPatternResponse(BaseModel):
    id: UUID
    pattern_type: str
    title: str
    description: Optional[str] = None
    evidence_message_ids: List[str] = []
    confidence: float = 0.5
    detected_at: datetime
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PatternListResponse(BaseModel):
    patterns: List[DetectedPatternResponse] = []
    total: int = 0


# === Timeline Reconstruction ===

class TimelineEvent(BaseModel):
    date: str
    description: str
    sources: List[str] = []
    significance: int = 1  # 1-5


class TimelineResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    topic: Optional[str] = None
    collection_id: Optional[UUID] = None
    events: List[TimelineEvent] = []
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    message_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TimelineListResponse(BaseModel):
    timelines: List[TimelineResponse] = []
    total: int = 0


class TimelineGenerateRequest(BaseModel):
    topic: Optional[str] = None
    collection_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
