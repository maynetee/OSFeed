from sqlalchemy import Column, BigInteger, String, DateTime, Text, Boolean, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
from app.models.collection import collection_channels
import uuid


class Channel(Base):
    __tablename__ = "channels"

    # Primary key as UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Telegram identifiers - BigInteger for large telegram IDs
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), index=True)
    title = Column(String(500))
    description = Column(Text, nullable=True)

    # Metadata
    detected_language = Column(String(10), nullable=True)
    subscriber_count = Column(BigInteger, default=0)
    is_active = Column(Boolean, default=True, index=True)

    # Fetch configuration (JSON - works with both SQLite and PostgreSQL)
    fetch_config = Column(
        JSON,
        default={"frequency_minutes": 5, "max_messages": 100},
        nullable=True
    )

    # Timestamps with timezone
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="channel", cascade="all, delete-orphan")
    collections = relationship("Collection", secondary=collection_channels, back_populates="channels")

    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_channels_active_username", "is_active", "username"),
    )
