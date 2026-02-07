import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class DigestPreference(Base):
    __tablename__ = "digest_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    enabled = Column(Boolean, default=False)
    frequency = Column(String(10), default="daily")  # daily, weekly
    send_hour = Column(Integer, default=8)  # 0-23 UTC
    collection_ids = Column(JSON, default=list)  # list of collection UUID strings
    max_messages = Column(Integer, default=20)  # 10, 20, 50
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
