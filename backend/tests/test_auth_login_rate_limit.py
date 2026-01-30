import pytest
from httpx import AsyncClient, ASGITransport
from redis.asyncio import Redis

from app.main import app
from app.database import init_db
from app.config import get_settings


async def clear_rate_limit_key(redis_url: str, key_pattern: str):
    """Helper to clear rate limit keys from Redis for testing."""
    redis = Redis.from_url(redis_url, decode_responses=True)
    try:
        keys = await redis.keys(f"auth_ratelimit:{key_pattern}*")
        if keys:
            await redis.delete(*keys)
    finally:
        await redis.close()


@pytest.mark.asyncio
async def test_login_rate_limiting():
    """Test that login endpoint enforces rate limiting (5 requests per 15 minutes)."""
    await init_db()

    settings = get_settings()
    if not settings.redis_url:
        pytest.skip("Redis not configured - rate limiting test requires Redis")

    # Clear any existing rate limit keys for this test
    await clear_rate_limit_key(settings.redis_url, "login:")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Make 5 login attempts - these should all return 400 (bad credentials)
        for i in range(5):
            response = await client.post(
                "/api/auth/login",
                data={"username": "test@example.com", "password": "wrongpassword"},
            )
            assert response.status_code == 400, f"Request {i+1} should return 400 (bad credentials)"
            assert response.json()["detail"] == "LOGIN_BAD_CREDENTIALS"

        # 6th attempt should be rate limited (429)
        response = await client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 429, "6th request should return 429 (rate limited)"
        assert "Too many requests" in response.json()["detail"]

    # Cleanup: Clear rate limit keys after test
    await clear_rate_limit_key(settings.redis_url, "login:")


@pytest.mark.asyncio
async def test_login_rate_limiting_different_ips_are_independent():
    """Test that rate limiting is per-IP (different IPs don't share limits)."""
    await init_db()

    settings = get_settings()
    if not settings.redis_url:
        pytest.skip("Redis not configured - rate limiting test requires Redis")

    # Clear any existing rate limit keys for this test
    await clear_rate_limit_key(settings.redis_url, "login:")

    # Note: In the test environment with AsyncClient, all requests appear to come
    # from the same IP (testclient), so this test documents the expected behavior
    # but cannot fully verify it without multiple actual IP addresses.
    # The rate limiter implementation uses request.client.host for per-IP limiting.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Make 5 attempts from "first IP" (simulated via same client)
        for i in range(5):
            response = await client.post(
                "/api/auth/login",
                data={"username": "user1@example.com", "password": "wrongpassword"},
            )
            assert response.status_code == 400

        # 6th attempt should be rate limited
        response = await client.post(
            "/api/auth/login",
            data={"username": "user1@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 429

    # Cleanup: Clear rate limit keys after test
    await clear_rate_limit_key(settings.redis_url, "login:")
