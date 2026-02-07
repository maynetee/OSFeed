import uuid
from datetime import datetime, timezone

from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

collection_channels = Table(
    "collection_channels",
    Base.metadata,
    Column("collection_id", UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True),
    Column("channel_id", UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True),
)


class Collection(Base):
    __tablename__ = "collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)
    icon = Column(String(50), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    is_global = Column(Boolean, default=False, nullable=False)
    is_curated = Column(Boolean, default=False, nullable=False, index=True)
    curator = Column(String(100), nullable=True)
    region = Column(String(50), nullable=True)
    topic = Column(String(50), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    last_curated_at = Column(DateTime(timezone=True), nullable=True)
    curated_channel_usernames = Column(JSON, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="SET NULL"), nullable=True)
    auto_assign_languages = Column(JSON, default=list, nullable=True)
    auto_assign_keywords = Column(JSON, default=list, nullable=True)
    auto_assign_tags = Column(JSON, default=list, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    channels = relationship("Channel", secondary=collection_channels, back_populates="collections")
    parent = relationship("Collection", remote_side=[id], backref="children")
