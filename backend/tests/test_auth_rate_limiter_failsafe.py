"""
Tests for fail-closed behavior of auth rate limiter when Redis is unavailable.

Verifies that authentication endpoints properly fail-closed (deny requests)
rather than fail-open (allow unlimited requests) when Redis is unavailable.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from redis.exceptions import ConnectionError as RedisConnectionError

from app.main import app
from app.database import init_db
from app.services.auth_rate_limiter import get_auth_rate_limiter, AuthRateLimiter


@pytest.mark.asyncio
async def test_get_auth_rate_limiter_raises_when_redis_not_configured(monkeypatch):
    """Test that get_auth_rate_limiter() raises RuntimeError when REDIS_URL not configured."""
    # Clear the singleton to force reinitialization
    import app.services.auth_rate_limiter
    app.services.auth_rate_limiter._auth_rate_limiter = None

    # Remove REDIS_URL from environment
    monkeypatch.delenv("REDIS_URL", raising=False)

    # Force settings reload
    from app.config import get_settings
    get_settings.cache_clear()

    # Verify that get_auth_rate_limiter raises RuntimeError
    with pytest.raises(RuntimeError, match="REDIS_URL not configured"):
        get_auth_rate_limiter()

    # Cleanup: restore settings cache
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_check_rate_limit_returns_503_on_redis_connection_error():
    """Test that check_rate_limit() raises HTTPException(503) when Redis connection fails."""
    # Create a limiter with an invalid Redis URL (unreachable)
    limiter = AuthRateLimiter("redis://invalid-host:9999")

    # Verify that connection errors result in 503
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await limiter.check_rate_limit(
            key="test:192.168.1.1",
            max_requests=5,
            window_seconds=900
        )

    assert exc_info.value.status_code == 503
    assert "Rate limiter unavailable" in str(exc_info.value.detail)


def _remove_rate_limiter_overrides():
    """Temporarily remove conftest rate limiter overrides so real dependencies run."""
    from app.services.auth_rate_limiter import (
        rate_limit_forgot_password,
        rate_limit_request_verify,
        rate_limit_register,
        rate_limit_login,
    )
    deps = [rate_limit_forgot_password, rate_limit_request_verify,
            rate_limit_register, rate_limit_login]
    saved = {d: app.dependency_overrides.pop(d) for d in deps if d in app.dependency_overrides}
    return saved, deps


def _restore_rate_limiter_overrides(saved):
    """Restore conftest rate limiter overrides."""
    app.dependency_overrides.update(saved)


@pytest.mark.asyncio
async def test_login_endpoint_returns_503_when_redis_unavailable():
    """Test that login endpoint returns 503 when Redis connection fails."""
    await init_db()
    saved, _ = _remove_rate_limiter_overrides()

    try:
        # Mock get_auth_rate_limiter to return a limiter with invalid Redis URL
        with patch('app.services.auth_rate_limiter.get_auth_rate_limiter') as mock_get_limiter:
            # Create a limiter with unreachable Redis
            mock_limiter = AuthRateLimiter("redis://invalid-host:9999")
            mock_get_limiter.return_value = mock_limiter

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/auth/login",
                    data={"username": "test@example.com", "password": "testpassword"},
                )

                # Should return 503, not allow the request through
                assert response.status_code == 503, \
                    f"Expected 503 (service unavailable), got {response.status_code}"
                assert "Rate limiter unavailable" in response.json()["detail"]
    finally:
        _restore_rate_limiter_overrides(saved)


@pytest.mark.asyncio
async def test_register_endpoint_returns_503_when_redis_unavailable():
    """Test that register endpoint returns 503 when Redis connection fails."""
    await init_db()
    saved, _ = _remove_rate_limiter_overrides()

    try:
        # Mock get_auth_rate_limiter to return a limiter with invalid Redis URL
        with patch('app.services.auth_rate_limiter.get_auth_rate_limiter') as mock_get_limiter:
            # Create a limiter with unreachable Redis
            mock_limiter = AuthRateLimiter("redis://invalid-host:9999")
            mock_get_limiter.return_value = mock_limiter

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/auth/register",
                    json={
                        "email": "newuser@example.com",
                        "password": "SecurePassword123!",
                        "full_name": "Test User"
                    },
                )

                # Should return 503, not allow the request through
                assert response.status_code == 503, \
                    f"Expected 503 (service unavailable), got {response.status_code}"
                assert "Rate limiter unavailable" in response.json()["detail"]
    finally:
        _restore_rate_limiter_overrides(saved)


@pytest.mark.asyncio
async def test_forgot_password_endpoint_returns_503_when_redis_unavailable():
    """Test that forgot-password endpoint returns 503 when Redis connection fails."""
    await init_db()
    saved, _ = _remove_rate_limiter_overrides()

    try:
        # Mock get_auth_rate_limiter to return a limiter with invalid Redis URL
        with patch('app.services.auth_rate_limiter.get_auth_rate_limiter') as mock_get_limiter:
            # Create a limiter with unreachable Redis
            mock_limiter = AuthRateLimiter("redis://invalid-host:9999")
            mock_get_limiter.return_value = mock_limiter

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/auth/forgot-password",
                    json={"email": "test@example.com"},
                )

                # Should return 503, not allow the request through
                assert response.status_code == 503, \
                    f"Expected 503 (service unavailable), got {response.status_code}"
                assert "Rate limiter unavailable" in response.json()["detail"]
    finally:
        _restore_rate_limiter_overrides(saved)


@pytest.mark.asyncio
async def test_request_verify_endpoint_returns_503_when_redis_unavailable():
    """Test that request-verify-token endpoint returns 503 when Redis connection fails."""
    await init_db()
    saved, _ = _remove_rate_limiter_overrides()

    try:
        # Mock get_auth_rate_limiter to return a limiter with invalid Redis URL
        with patch('app.services.auth_rate_limiter.get_auth_rate_limiter') as mock_get_limiter:
            # Create a limiter with unreachable Redis
            mock_limiter = AuthRateLimiter("redis://invalid-host:9999")
            mock_get_limiter.return_value = mock_limiter

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/auth/request-verify-token",
                    json={"email": "test@example.com"},
                )

                # Should return 503, not allow the request through
                assert response.status_code == 503, \
                    f"Expected 503 (service unavailable), got {response.status_code}"
                assert "Rate limiter unavailable" in response.json()["detail"]
    finally:
        _restore_rate_limiter_overrides(saved)


@pytest.mark.asyncio
async def test_redis_incr_failure_returns_503():
    """Test that Redis operation failures (like incr) result in 503, not silent failure."""
    # Create a limiter and mock the Redis client to raise errors
    limiter = AuthRateLimiter("redis://localhost:6379")

    # Mock _get_redis to return a mock that raises connection errors
    mock_redis = AsyncMock()
    mock_redis.incr.side_effect = RedisConnectionError("Connection refused")

    with patch.object(limiter, '_get_redis', return_value=mock_redis):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check_rate_limit(
                key="test:192.168.1.1",
                max_requests=5,
                window_seconds=900
            )

        assert exc_info.value.status_code == 503
        assert "Rate limiter unavailable" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_redis_generic_exception_returns_503():
    """Test that any unexpected Redis exception results in 503, not silent failure."""
    # Create a limiter and mock the Redis client to raise generic errors
    limiter = AuthRateLimiter("redis://localhost:6379")

    # Mock _get_redis to return a mock that raises generic exceptions
    mock_redis = AsyncMock()
    mock_redis.incr.side_effect = Exception("Unexpected Redis error")

    with patch.object(limiter, '_get_redis', return_value=mock_redis):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check_rate_limit(
                key="test:192.168.1.1",
                max_requests=5,
                window_seconds=900
            )

        assert exc_info.value.status_code == 503
        assert "Rate limiter unavailable" in str(exc_info.value.detail)
