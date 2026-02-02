import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from fastapi_users.password import PasswordHelper
from fastapi_users.jwt import generate_jwt

from app.main import app
from app.database import AsyncSessionLocal, init_db
from app.models.user import User
from app.config import get_settings

settings = get_settings()


@pytest.mark.asyncio
async def test_register_and_verify_flow():
    """Test full register + email verification flow."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register a new user
        with patch("app.auth.users.email_service") as mock_email:
            mock_email.send_verification = AsyncMock()
            register_response = await client.post(
                "/api/auth/register",
                json={
                    "email": "verify_flow@example.com",
                    "password": "StrongPass123!",
                },
            )
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["email"] == "verify_flow@example.com"
        assert user_data["is_verified"] is False

        # Login should fail for unverified user if fastapi-users enforces it,
        # but our custom login endpoint only checks is_active, not is_verified.
        # Still, let's verify the user exists unverified.
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.email == "verify_flow@example.com")
            )
            user = result.scalars().first()
            assert user is not None
            assert user.is_verified is False
            user_id = str(user.id)

        # Generate a verification token (same way UserManager does)
        token = generate_jwt(
            data={
                "sub": user_id,
                "email": "verify_flow@example.com",
                "aud": "fastapi-users:verify",
            },
            secret=settings.secret_key,
            lifetime_seconds=86400,
        )

        # Verify the user
        verify_response = await client.post(
            "/api/auth/verify",
            json={"token": token},
        )
        assert verify_response.status_code == 200

        # Confirm user is now verified in DB
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.email == "verify_flow@example.com")
            )
            user = result.scalars().first()
            assert user.is_verified is True


@pytest.mark.asyncio
async def test_forgot_and_reset_password_flow():
    """Test full forgot-password + reset-password flow."""
    await init_db()
    password_helper = PasswordHelper()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == "reset_flow@example.com")
        )
        if not result.scalars().first():
            user = User(
                email="reset_flow@example.com",
                hashed_password=password_helper.hash("OldPassword123!"),
                is_active=True,
                is_superuser=False,
                is_verified=True,
            )
            session.add(user)
            await session.commit()

    # Get user id for token generation
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == "reset_flow@example.com")
        )
        user = result.scalars().first()
        user_id = str(user.id)
        old_hash = user.hashed_password

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Request forgot password (should succeed even without email enabled)
        with patch("app.auth.users.email_service") as mock_email:
            mock_email.send_password_reset = AsyncMock()
            forgot_response = await client.post(
                "/api/auth/forgot-password",
                json={"email": "reset_flow@example.com"},
            )
        # FastAPI-Users returns 202 for forgot-password
        assert forgot_response.status_code == 202

        # Generate reset token the same way FastAPI-Users does internally
        token = generate_jwt(
            data={
                "sub": user_id,
                "password_fgpt": password_helper.hash(old_hash),
                "aud": "fastapi-users:reset",
            },
            secret=settings.secret_key,
            lifetime_seconds=3600,
        )

        # Reset password
        reset_response = await client.post(
            "/api/auth/reset-password",
            json={"token": token, "password": "NewPassword456!"},
        )
        assert reset_response.status_code == 200

        # Login with new password should work
        login_response = await client.post(
            "/api/auth/login",
            data={"username": "reset_flow@example.com", "password": "NewPassword456!"},
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()


@pytest.mark.asyncio
async def test_login_blocked_for_inactive_user():
    """Test that login is blocked for inactive users."""
    await init_db()
    password_helper = PasswordHelper()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == "inactive_user@example.com")
        )
        if not result.scalars().first():
            user = User(
                email="inactive_user@example.com",
                hashed_password=password_helper.hash("password123"),
                is_active=False,
                is_superuser=False,
                is_verified=True,
            )
            session.add(user)
            await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_response = await client.post(
            "/api/auth/login",
            data={"username": "inactive_user@example.com", "password": "password123"},
        )
        assert login_response.status_code == 400


@pytest.mark.asyncio
async def test_rate_limiting_returns_429():
    """Test that rate limiting returns 429 when limit exceeded."""
    await init_db()

    from fastapi import HTTPException, status
    from app.services.auth_rate_limiter import rate_limit_forgot_password

    async def raise_429():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Try again in 900 seconds.",
        )

    previous_override = app.dependency_overrides.get(rate_limit_forgot_password)
    app.dependency_overrides[rate_limit_forgot_password] = raise_429

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/forgot-password",
                json={"email": "anyone@example.com"},
            )
            assert response.status_code == 429
            assert "Too many requests" in response.json()["detail"]
    finally:
        if previous_override is not None:
            app.dependency_overrides[rate_limit_forgot_password] = previous_override
        else:
            app.dependency_overrides.pop(rate_limit_forgot_password, None)


@pytest.mark.asyncio
async def test_verify_rejects_invalid_token():
    """Test that verify endpoint rejects invalid tokens."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/verify",
            json={"token": "invalid-token-value"},
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_rejects_invalid_token():
    """Test that reset-password endpoint rejects invalid tokens."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/reset-password",
            json={"token": "invalid-token", "password": "NewPassword123!"},
        )
        assert response.status_code == 400
