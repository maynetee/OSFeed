from fastapi_users import schemas
from pydantic import EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole


class UserRead(schemas.BaseUser[UUID]):
    """Schema for reading user data."""
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    preferred_language: str = "en"
    consent_given_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a new user."""
    full_name: Optional[str] = None
    # role field removed per security fix - prevents clients from specifying role
    preferred_language: str = "en"
    consent_given_at: Optional[datetime] = None  # Set when user accepts terms


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating user data."""
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    preferred_language: Optional[str] = None
    data_retention_days: Optional[int] = None
