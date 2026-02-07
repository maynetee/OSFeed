from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, String, DateTime, Integer, Enum as SQLEnum
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
    username = Column(String(20), unique=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    country = Column(String(2), nullable=True)
    role = Column(
        SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.VIEWER,
        nullable=False
    )
    preferred_language = Column(String(10), default="en", nullable=False)

    # RGPD compliance fields
    consent_given_at = Column(DateTime(timezone=True), nullable=True)
    data_retention_days = Column(Integer, default=365)

    # Activity tracking
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Stripe subscription
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    subscription_plan = Column(String(20), default="none")  # solo, team, enterprise, none
    subscription_status = Column(String(20), default="none")  # active, canceled, past_due, trialing, none
    subscription_period_end = Column(DateTime(timezone=True), nullable=True)

    # Refresh token (hashed)
    refresh_token_hash = Column(String(128), nullable=True)
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"
