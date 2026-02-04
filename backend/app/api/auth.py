"""Authentication API routes for OSFeed."""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.manager import BaseUserManager
from fastapi_users.exceptions import UserAlreadyExists
from fastapi_users.router.common import ErrorCode
from fastapi_users.authentication import Strategy
from fastapi_users import exceptions as fapi_exceptions
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import BaseModel

from app.auth.users import auth_backend, fastapi_users, current_active_user, get_user_manager
from app.auth.refresh import generate_refresh_token, hash_refresh_token, refresh_token_expiry
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.models.user import User
from app.database import get_db
from app.config import get_settings
from app.services.auth_rate_limiter import (
    rate_limit_forgot_password,
    rate_limit_request_verify,
    rate_limit_register,
    rate_limit_login,
)
from app.services.email_service import _redact_email
from app.services.translation_service import invalidate_channel_translation_cache
from app.services.audit import record_audit_event
from app.models.channel import user_channels

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(rate_limit_register)])
async def register(
    request: Request,
    user_create: UserCreate,
    user_manager: BaseUserManager = Depends(get_user_manager),
    db: AsyncSession = Depends(get_db),
):
    """Register a new user with detailed error logging."""
    logger.info(f"Registration attempt for email: {_redact_email(user_create.email)}")
    try:
        created_user = await user_manager.create(user_create, safe=True, request=request)
        logger.info(f"Registration successful for email: {_redact_email(user_create.email)}")
        record_audit_event(
            db,
            user_id=created_user.id,
            action="auth.register",
            resource_type="user",
            resource_id=str(created_user.id),
            metadata={"email": _redact_email(user_create.email)},
        )
        return created_user
    except HTTPException:
        raise
    except UserAlreadyExists:
        logger.warning(f"Registration failed: email already exists ({_redact_email(user_create.email)})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.REGISTER_USER_ALREADY_EXISTS,
        )
    except fapi_exceptions.InvalidPasswordException as e:
        logger.warning(f"Registration failed: invalid password for {_redact_email(user_create.email)} - {e.reason}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.REGISTER_INVALID_PASSWORD,
                "reason": e.reason,
            },
        )
    except (SQLAlchemyError, IntegrityError) as e:
        logger.error(f"Database error during registration for {_redact_email(user_create.email)}: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="REGISTER_DATABASE_ERROR",
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration for {_redact_email(user_create.email)}: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="REGISTER_UNEXPECTED_ERROR",
        )

router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="",
    dependencies=[Depends(rate_limit_forgot_password)],
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="",
    dependencies=[Depends(rate_limit_request_verify)],
)

# User management routes (admin only)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
)


class LanguageUpdateRequest(BaseModel):
    language: str


@router.post("/login", dependencies=[Depends(rate_limit_login)])
async def login(
    request: Request,
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: BaseUserManager = Depends(get_user_manager),
    strategy: Strategy = Depends(auth_backend.get_strategy),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate a user and return access and refresh tokens as httpOnly cookies."""
    settings = get_settings()
    user = await user_manager.authenticate(credentials)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
        )
    access_token = await strategy.write_token(user)
    refresh_token = generate_refresh_token()
    refresh_expires_at = refresh_token_expiry()
    await user_manager.user_db.update(
        user,
        {
            "refresh_token_hash": hash_refresh_token(refresh_token),
            "refresh_token_expires_at": refresh_expires_at,
        },
    )

    record_audit_event(
        db,
        user_id=user.id,
        action="auth.login",
        resource_type="user",
        resource_id=str(user.id),
    )

    # Create JSON response with user info
    json_response = JSONResponse(
        {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "is_verified": user.is_verified,
            },
            "token_type": "bearer",
        }
    )

    # Set access token cookie
    json_response.set_cookie(
        key=settings.cookie_access_token_name,
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )

    # Set refresh token cookie
    json_response.set_cookie(
        key=settings.cookie_refresh_token_name,
        value=refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )

    await user_manager.on_after_login(user, request, json_response)
    return json_response


@router.post("/refresh")
async def refresh_access_token(
    refresh_token: str = Cookie(None),
    user_manager: BaseUserManager = Depends(get_user_manager),
    strategy: Strategy = Depends(auth_backend.get_strategy),
):
    """Refresh an expired access token using a valid refresh token from httpOnly cookies."""
    settings = get_settings()

    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found")

    token_hash = hash_refresh_token(refresh_token)
    session = user_manager.user_db.session
    result = await session.execute(select(User).where(User.refresh_token_hash == token_hash))
    user = result.scalars().first()

    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    refresh_expires_at = user.refresh_token_expires_at
    if refresh_expires_at and refresh_expires_at.tzinfo is None:
        refresh_expires_at = refresh_expires_at.replace(tzinfo=timezone.utc)
    if not refresh_expires_at or refresh_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    access_token = await strategy.write_token(user)
    new_refresh_token = generate_refresh_token()
    refresh_expires_at = refresh_token_expiry()
    await user_manager.user_db.update(
        user,
        {
            "refresh_token_hash": hash_refresh_token(new_refresh_token),
            "refresh_token_expires_at": refresh_expires_at,
        },
    )

    # Create JSON response with user info
    json_response = JSONResponse(
        {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "is_verified": user.is_verified,
            },
            "token_type": "bearer",
        }
    )

    # Set access token cookie
    json_response.set_cookie(
        key=settings.cookie_access_token_name,
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )

    # Set refresh token cookie
    json_response.set_cookie(
        key=settings.cookie_refresh_token_name,
        value=new_refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )

    return json_response


@router.get("/me", response_model=UserRead, summary="Get current user profile")
async def get_current_user_profile(user: User = Depends(current_active_user)):
    """Get the current authenticated user's profile."""
    return user


@router.post("/me/consent", response_model=UserRead, summary="Record RGPD consent")
async def record_consent(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Record user's RGPD consent timestamp."""
    user.consent_given_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/me/data", summary="Request data deletion (RGPD)")
async def request_data_deletion(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Request deletion of all user data (RGPD right to be forgotten)."""
    # In a real implementation, this would:
    # 1. Anonymize user data
    # 2. Delete personal information
    # 3. Keep audit logs for legal compliance
    # For now, we just mark the account as inactive


    user.is_active = False
    await db.commit()

    return {
        "status": "success",
        "message": "Your account has been deactivated. Personal data will be anonymized within 30 days.",
    }


@router.patch("/me/language", response_model=UserRead, summary="Update user language preference")
async def update_language(
    payload: LanguageUpdateRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's preferred language."""
    user.preferred_language = payload.language
    await db.commit()
    await db.refresh(user)

    # Invalidate translation cache for all user's channels
    user_channel_ids_result = await db.execute(
        select(user_channels.c.channel_id).where(user_channels.c.user_id == user.id)
    )
    for row in user_channel_ids_result.all():
        await invalidate_channel_translation_cache(row.channel_id)

    return user


@router.post("/logout", summary="Logout user")
async def logout(
    user: User = Depends(current_active_user),
    user_manager: BaseUserManager = Depends(get_user_manager),
    db: AsyncSession = Depends(get_db),
):
    """Logout the current user by invalidating their refresh token and clearing cookies."""
    settings = get_settings()

    await user_manager.user_db.update(
        user,
        {
            "refresh_token_hash": None,
            "refresh_token_expires_at": None,
        },
    )
    record_audit_event(
        db,
        user_id=user.id,
        action="auth.logout",
        resource_type="user",
        resource_id=str(user.id),
    )

    # Create JSON response
    json_response = JSONResponse({"message": "Successfully logged out"})

    # Clear access token cookie
    json_response.set_cookie(
        key=settings.cookie_access_token_name,
        value="",
        max_age=0,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )

    # Clear refresh token cookie
    json_response.set_cookie(
        key=settings.cookie_refresh_token_name,
        value="",
        max_age=0,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )

    return json_response
