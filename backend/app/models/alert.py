from sqlalchemy import Column, DateTime, String, ForeignKey, Boolean, Integer, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
import uuid


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    keywords = Column(JSON, default=list, nullable=True)
    entities = Column(JSON, default=list, nullable=True)
    min_threshold = Column(Integer, default=1)
    frequency = Column(String(20), default="daily")
    notification_channels = Column(JSON, default=lambda: ["in_app"], nullable=True)
    match_mode = Column(String(10), default="any", nullable=False)
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    last_evaluated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    collection = relationship("Collection")
    triggers = relationship("AlertTrigger", back_populates="alert", cascade="all, delete-orphan")


class AlertTrigger(Base):
    __tablename__ = "alert_triggers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    triggered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    message_ids = Column(JSON, nullable=False)
    summary = Column(Text, nullable=True)

    alert = relationship("Alert", back_populates="triggers")
