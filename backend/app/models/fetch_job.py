from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
import uuid


class FetchJob(Base):
    __tablename__ = "fetch_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), index=True, nullable=False)

    days = Column(Integer, nullable=False, default=3)
    status = Column(String(20), nullable=False, default="queued", index=True)
    stage = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    total_messages = Column(Integer, nullable=True)
    new_messages = Column(Integer, nullable=True)
    processed_messages = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    channel = relationship("Channel", back_populates="fetch_jobs")

    __table_args__ = (
        Index("ix_fetch_jobs_channel_created", "channel_id", "created_at"),
    )
