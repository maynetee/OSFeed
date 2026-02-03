"""FastAPI-Users configuration for OSFeed."""
import asyncio
import logging
import re
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users.exceptions import InvalidPasswordException
from fastapi_users.jwt import generate_jwt
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.email_service import email_service, _redact_email

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
    verification_token_audience = "fastapi-users:verify"
    verification_token_lifetime_seconds = 86400  # 24 hours

    async def validate_password(
        self,
        password: str,
        user: Optional[User] = None,
    ) -> None:
        """
        Validate password against OWASP-recommended strength requirements.

        Requirements:
        - Minimum 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 digit
        - At least 1 special character

        Args:
            password: The password to validate
            user: Optional user object (unused, but part of base signature)

        Raises:
            InvalidPasswordException: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise InvalidPasswordException(
                reason="Password must be at least 8 characters long"
            )

        if not re.search(r"[A-Z]", password):
            raise InvalidPasswordException(
                reason="Password must contain at least one uppercase letter"
            )

        if not re.search(r"[a-z]", password):
            raise InvalidPasswordException(
                reason="Password must contain at least one lowercase letter"
            )

        if not re.search(r"\d", password):
            raise InvalidPasswordException(
                reason="Password must contain at least one digit"
            )

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise InvalidPasswordException(
                reason="Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
            )

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Called after a user successfully registers. Sends verification email."""
        logger.info(f"User {_redact_email(user.email)} has registered.")
        if settings.email_enabled:
            # Generate verification token manually (FastAPI-Users doesn't pass it here)
            token_data = {
                "sub": str(user.id),
                "email": user.email,
                "aud": self.verification_token_audience,
            }
            token = generate_jwt(
                data=token_data,
                secret=self.verification_token_secret,
                lifetime_seconds=self.verification_token_lifetime_seconds,
            )
            # Send email in background (non-blocking)
            try:
                asyncio.create_task(email_service.send_verification(user.email, token))
                logger.info(f"Verification email task created for {_redact_email(user.email)}")
            except RuntimeError as e:
                logger.error(f"Failed to create verification email task for {_redact_email(user.email)} (event loop error): {e}")
            except Exception as e:
                logger.error(f"Failed to create verification email task for {_redact_email(user.email)}: {e}")
        else:
            logger.warning(f"Email disabled - skipping verification email for {_redact_email(user.email)}")

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response=None,
    ):
        """Called after a user successfully logs in."""
        # Update last login timestamp
        user.last_login_at = datetime.now(timezone.utc)
        logger.info(f"User {_redact_email(user.email)} logged in.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after a password reset token is generated. Sends reset email."""
        logger.info(f"User {_redact_email(user.email)} has requested a password reset.")
        if settings.email_enabled:
            # Token is passed by FastAPI-Users for this hook
            try:
                asyncio.create_task(email_service.send_password_reset(user.email, token))
                logger.info(f"Password reset email task created for {_redact_email(user.email)}")
            except RuntimeError as e:
                logger.error(f"Failed to create password reset email task for {_redact_email(user.email)} (event loop error): {e}")
            except Exception as e:
                logger.error(f"Failed to create password reset email task for {_redact_email(user.email)}: {e}")
        else:
            logger.warning(f"Email disabled - skipping password reset email for {_redact_email(user.email)}")

    async def on_after_reset_password(
        self, user: User, request: Optional[Request] = None
    ):
        """Called after a password is successfully reset."""
        logger.info(f"User {_redact_email(user.email)} has reset their password.")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called when user explicitly requests verification email."""
        logger.info(f"Verification requested for {_redact_email(user.email)}.")
        if settings.email_enabled:
            # Token is passed by FastAPI-Users for this hook
            try:
                asyncio.create_task(email_service.send_verification(user.email, token))
                logger.info(f"Verification email task created for {_redact_email(user.email)}")
            except RuntimeError as e:
                logger.error(f"Failed to create verification email task for {_redact_email(user.email)} (event loop error): {e}")
            except Exception as e:
                logger.error(f"Failed to create verification email task for {_redact_email(user.email)}: {e}")
        else:
            logger.warning(f"Email disabled - skipping verification email for {_redact_email(user.email)}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """Get the user manager instance."""
    yield UserManager(user_db)


# Cookie Transport (httpOnly cookies for security)
cookie_transport = CookieTransport(
    cookie_name=settings.cookie_access_token_name,
    cookie_max_age=settings.access_token_expire_minutes * 60,
    cookie_secure=settings.cookie_secure,
    cookie_httponly=True,
    cookie_samesite=settings.cookie_samesite,
)


def get_jwt_strategy() -> JWTStrategy:
    """Create JWT strategy with configured settings."""
    return JWTStrategy(
        secret=settings.secret_key,
        lifetime_seconds=settings.access_token_expire_minutes * 60,
    )


# Authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
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
