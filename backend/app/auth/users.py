"""FastAPI-Users configuration for OSFeed."""
import logging
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User

settings = get_settings()
logger = logging.getLogger(__name__)


# Database adapter for FastAPI-Users
async def get_user_db(session: AsyncSession = Depends(get_db)):
    """Get the SQLAlchemy user database adapter."""
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    """Custom user manager with additional logic."""

    reset_password_token_secret = settings.secret_key
    verification_token_secret = settings.secret_key

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Called after a user successfully registers."""
        logger.info(f"User {user.email} has registered.")

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response=None,
    ):
        """Called after a user successfully logs in."""
        # Update last login timestamp
        user.last_login_at = datetime.now(timezone.utc)
        logger.info(f"User {user.email} logged in.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after a password reset token is generated."""
        logger.info(f"User {user.email} has requested a password reset. Token: {token}")

    async def on_after_reset_password(
        self, user: User, request: Optional[Request] = None
    ):
        """Called after a password is successfully reset."""
        logger.info(f"User {user.email} has reset their password.")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """Get the user manager instance."""
    yield UserManager(user_db)


# JWT Transport (Bearer token in Authorization header)
bearer_transport = BearerTransport(tokenUrl="api/auth/login")


def get_jwt_strategy() -> JWTStrategy:
    """Create JWT strategy with configured settings."""
    return JWTStrategy(
        secret=settings.secret_key,
        lifetime_seconds=settings.access_token_expire_minutes * 60,
    )


# Authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPI-Users instance
fastapi_users = FastAPIUsers[User, UUID](
    get_user_manager,
    [auth_backend],
)

# Dependency to get current active user
current_active_user = fastapi_users.current_user(active=True)

# Dependency to get current superuser
current_superuser = fastapi_users.current_user(active=True, superuser=True)
