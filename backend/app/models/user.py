from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, String, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User model with FastAPI-Users integration and RGPD compliance fields."""
    __tablename__ = "users"

    # Profile information
    full_name = Column(String(255), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)

    # RGPD compliance fields
    consent_given_at = Column(DateTime(timezone=True), nullable=True)
    data_retention_days = Column(Integer, default=365)

    # Activity tracking
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Refresh token (hashed)
    refresh_token_hash = Column(String(128), nullable=True)
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    summaries = relationship("Summary", backref="user", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"
