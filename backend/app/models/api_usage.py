from sqlalchemy import Column, DateTime, String, Integer, JSON, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.database import Base
import uuid


class ApiUsage(Base):
    __tablename__ = "api_usages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)
    purpose = Column(String(50), nullable=False, index=True)
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost_usd = Column(Numeric(12, 6), nullable=False, default=0)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("ix_api_usages_provider_model_time", "provider", "model", "created_at"),
    )
