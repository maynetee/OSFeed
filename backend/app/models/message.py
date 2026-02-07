import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    # Primary key as UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to channel (UUID)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), index=True, nullable=False)

    # Telegram message ID - BigInteger for large IDs
    telegram_message_id = Column(BigInteger, nullable=False)

    # Content
    original_text = Column(Text)
    translated_text = Column(Text, nullable=True)
    needs_translation = Column(Boolean, default=True, index=True, nullable=False)
    source_language = Column(String(10), nullable=True)
    target_language = Column(String(10), default="fr")
    translation_priority = Column(String(10), default="normal", nullable=False)

    # Media information (JSON - works with both SQLite and PostgreSQL)
    media_type = Column(String(50), nullable=True)  # photo, video, document, audio
    media_urls = Column(JSON, nullable=True)  # ["url1", "url2", ...]

    # Deduplication
    is_duplicate = Column(Boolean, default=False, index=True)
    originality_score = Column(SmallInteger, default=100)  # 0-100
    duplicate_group_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Relevance scoring
    relevance_score = Column(Float, nullable=True, index=True)

    # Timestamps with timezone
    published_at = Column(DateTime(timezone=True), index=True)
    fetched_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    translated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    channel = relationship("Channel", back_populates="messages")
    translations = relationship("MessageTranslation", back_populates="message", cascade="all, delete-orphan")

    # Composite indexes for common queries
    __table_args__ = (
        # Unique constraint: one message per channel
        Index("ix_messages_channel_telegram_id", "channel_id", "telegram_message_id", unique=True),
        # For timeline queries
        Index("ix_messages_channel_published", "channel_id", "published_at"),
        Index("ix_messages_channel_published_id", "channel_id", "published_at", "id"),
        # For duplicate analysis
        Index("ix_messages_duplicate_group", "duplicate_group_id", postgresql_where=duplicate_group_id.isnot(None)),
        # For translation job queries (OPTIMIZATION_PLAN.md Phase 2)
        Index("ix_messages_translation_query", "channel_id", "needs_translation", "translation_priority"),
        # For stats queries (OPTIMIZATION_PLAN.md Phase 2)
        Index("ix_messages_stats_query", "published_at", "is_duplicate"),
        # Composite index for filtered timeline queries (channel + date + dedup)
        Index("ix_messages_channel_published_dedup", "channel_id", "published_at", "is_duplicate"),
        # For language distribution analytics queries
        Index("ix_messages_source_language", "source_language"),
        # For collection stats analytics (channel + date + language)
        Index("ix_messages_channel_published_lang", "channel_id", "published_at", "source_language"),
        # Fulltext GIN index on message text for search queries (PostgreSQL only)
        Index(
            "ix_messages_text_search",
            "original_text",
            "translated_text",
            postgresql_using="gin",
            postgresql_ops={"original_text": "gin_trgm_ops", "translated_text": "gin_trgm_ops"},
        ),
    )


class MessageTranslation(Base):
    """
    Cache for message translations in multiple languages.
    
    Optimization from OPTIMIZATION_PLAN.md Phase 5:
    - Check this table before calling GPT API for translations
    - 100 users requesting same message in French = 1 GPT call + 99 DB lookups
    - Estimated savings: 99x fewer GPT API calls for popular messages
    """
    __tablename__ = "message_translations"

    # Primary key as UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to the original message
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)

    # Target language code (e.g., "en", "fr", "de", "es")
    target_lang = Column(String(10), nullable=False)

    # The translated text
    translated_text = Column(Text, nullable=False)

    # When the translation was created
    translated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # User who triggered the translation (nullable for system-generated)
    translated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Track token usage for analytics
    token_count = Column(Integer, nullable=True)

    # Relationships
    message = relationship("Message", back_populates="translations")

    # Unique constraint and indexes matching the migration
    __table_args__ = (
        # One translation per message per target language
        UniqueConstraint("message_id", "target_lang", name="uq_message_translations_message_lang"),
        # Composite index for fast lookup of cached translations
        Index("ix_message_translations_lookup", "message_id", "target_lang"),
        # Index for finding all translations for a message
        Index("ix_message_translations_message_id", "message_id"),
    )
