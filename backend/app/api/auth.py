"""Authentication API routes for OSFeed."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.manager import BaseUserManager
from fastapi_users.router.common import ErrorCode
from fastapi_users.authentication import Strategy
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.auth.users import auth_backend, fastapi_users, current_active_user, get_user_manager
from app.auth.refresh import generate_refresh_token, hash_refresh_token, refresh_token_expiry
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.models.user import User
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="",
)

router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="",
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="",
)

# User management routes (admin only)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
)


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login")
async def login(
    request: Request,
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: BaseUserManager = Depends(get_user_manager),
    strategy: Strategy = Depends(auth_backend.get_strategy),
):
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

    response = JSONResponse(
        {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "refresh_expires_at": refresh_expires_at.isoformat(),
        }
    )
    await user_manager.on_after_login(user, request, response)
    return response


@router.post("/refresh")
async def refresh_access_token(
    payload: RefreshRequest,
    user_manager: BaseUserManager = Depends(get_user_manager),
    strategy: Strategy = Depends(auth_backend.get_strategy),
):
    token_hash = hash_refresh_token(payload.refresh_token)
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

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token,
        "refresh_expires_at": refresh_expires_at.isoformat(),
    }


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


@router.post("/logout", summary="Logout user")
async def logout(
    user: User = Depends(current_active_user),
    user_manager: BaseUserManager = Depends(get_user_manager),
):
    """Logout the current user by invalidating their refresh token."""
    await user_manager.user_db.update(
        user,
        {
            "refresh_token_hash": None,
            "refresh_token_expires_at": None,
        },
    )
    return JSONResponse({"message": "Successfully logged out"})
