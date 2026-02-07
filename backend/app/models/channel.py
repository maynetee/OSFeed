import uuid
from datetime import datetime, timezone

from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy import JSON, BigInteger, Boolean, Column, DateTime, ForeignKey, Index, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.collection import collection_channels

# Junction table for many-to-many user-channel relationship
# Enables shared channel data: when user B adds a channel user A already added,
# the system can link to existing channel instead of re-fetching from Telegram
user_channels = Table(
    "user_channels",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("channel_id", UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("added_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
)


class Channel(Base):
    __tablename__ = "channels"

    # Primary key as UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Telegram identifiers - BigInteger for large telegram IDs
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    username = Column(String(255), index=True)
    title = Column(String(500))
    description = Column(Text, nullable=True)

    # Metadata
    detected_language = Column(String(10), nullable=True)
    subscriber_count = Column(BigInteger, default=0)
    is_active = Column(Boolean, default=True, index=True)
    tags = Column(JSON, default=list, nullable=True)
    region = Column(String(50), nullable=True, index=True)
    topics = Column(JSON, default=list, nullable=True)

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
    fetch_jobs = relationship("FetchJob", back_populates="channel", cascade="all, delete-orphan")
    users = relationship("User", secondary=user_channels, backref="channels")

    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_channels_active_username", "is_active", "username"),
    )
