from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from fastapi_users_db_sqlalchemy.generics import GUID
from datetime import datetime, timezone
from app.database import Base


class CollectionShare(Base):
    __tablename__ = "collection_shares"

    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    permission = Column(String(20), default="viewer")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
