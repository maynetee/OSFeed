"""Analysis models for intelligence features: escalation scoring, cross-source correlation,
pattern detection, and timeline reconstruction."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class EscalationScore(Base):
    """Escalation score for a message, computed by LLM analysis."""
    __tablename__ = "escalation_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    score = Column(Float, nullable=False)  # 0.0 - 1.0
    level = Column(String(10), nullable=False)  # high, medium, low
    factors = Column(JSON, default=list)  # ["reason1", "reason2"]
    computed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_escalation_scores_level", "level"),
        Index("ix_escalation_scores_score", "score"),
    )


class Correlation(Base):
    """Cross-source correlation analysis for duplicate message groups."""
    __tablename__ = "correlations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    duplicate_group_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    analysis_text = Column(Text, nullable=True)
    consistent_facts = Column(JSON, default=list)
    unique_details = Column(JSON, default=list)
    contradictions = Column(JSON, default=list)
    source_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class DetectedPattern(Base):
    """Detected intelligence pattern (volume spike, narrative shift, etc.)."""
    __tablename__ = "detected_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_type = Column(String(30), nullable=False)  # volume_spike, narrative_shift, entity_emergence
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    evidence_message_ids = Column(JSON, default=list)  # list of UUID strings
    confidence = Column(Float, nullable=False, default=0.5)  # 0.0 - 1.0
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_detected_patterns_type", "pattern_type"),
        Index("ix_detected_patterns_detected_at", "detected_at"),
    )


class Timeline(Base):
    """User-generated timeline reconstruction from intelligence messages."""
    __tablename__ = "timelines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(300), nullable=False)
    topic = Column(String(200), nullable=True)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="SET NULL"), nullable=True)
    events = Column(JSON, default=list)  # [{date, description, sources, significance}]
    date_range_start = Column(DateTime(timezone=True), nullable=True)
    date_range_end = Column(DateTime(timezone=True), nullable=True)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
