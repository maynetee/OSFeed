from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Float, Integer, Table, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base

class NarrativeCluster(Base):
    __tablename__ = "narrative_clusters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    title = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    
    structured_summary = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    message_count = Column(Integer, default=0)
    channel_count = Column(Integer, default=0)
    
    first_message_at = Column(DateTime(timezone=True), nullable=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True)

    primary_source_channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id", ondelete="SET NULL"), nullable=True)
    
    sentiment_score = Column(Float, nullable=True)
    urgency_score = Column(Integer, nullable=True)
    
    velocity = Column(Float, default=0.0)
    emergence_score = Column(Float, default=0.0)
    
    messages = relationship("Message", back_populates="cluster")
    primary_source_channel = relationship("Channel")
