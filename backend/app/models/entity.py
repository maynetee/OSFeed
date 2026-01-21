from sqlalchemy import Column, String, ForeignKey, Table, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

# Association table for Many-to-Many relationship
message_entity_association = Table(
    "message_entity_association",
    Base.metadata,
    Column("message_id", UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True),
    Column("entity_id", UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True),
)

class Entity(Base):
    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    
    frequency = Column(Integer, default=1)
    
    messages = relationship("Message", secondary=message_entity_association, back_populates="entities_rel")

    __table_args__ = (
        UniqueConstraint('name', 'type', name='uq_entity_name_type'),
    )
