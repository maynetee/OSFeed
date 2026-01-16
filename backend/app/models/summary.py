from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.database import Base
import uuid


class Summary(Base):
    """Daily/weekly digests generated from collected messages."""
    __tablename__ = "summaries"

    # Primary key as UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Optional user association (for personalized digests)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Summary metadata
    digest_type = Column(String(50), index=True, default="daily")  # daily, weekly, custom
    title = Column(String(500), nullable=True)

    # Content
    content = Column(Text)  # Plain text summary
    content_html = Column(Text, nullable=True)  # HTML formatted version
    entities = Column(
        JSON,
        default={"persons": [], "locations": [], "organizations": []},
        nullable=True,
    )

    # Statistics
    message_count = Column(Integer, default=0)
    channels_covered = Column(Integer, default=0)
    duplicates_filtered = Column(Integer, default=0)

    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Filters used to generate this summary (JSON - works with both SQLite and PostgreSQL)
    filters = Column(
        JSON,
        default={"collections": [], "languages": [], "keywords": []},
        nullable=True
    )

    # Timestamps
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Composite indexes
    __table_args__ = (
        Index("ix_summaries_user_type_date", "user_id", "digest_type", "generated_at"),
    )
