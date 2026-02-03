"""Rate limiter for auth endpoints using Redis."""
import logging
from typing import Optional

from redis.asyncio import Redis
from redis.exceptions import RedisError
from fastapi import HTTPException, Request, status

from app.config import get_settings

logger = logging.getLogger(__name__)


class AuthRateLimiter:
    """Simple Redis-based rate limiter for auth endpoints."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis: Optional[Redis] = None

    async def _get_redis(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        """
        Check if request is within rate limit.

        Returns True if allowed, raises HTTPException if rate limited.
        """
        try:
            redis = await self._get_redis()
            full_key = f"auth_ratelimit:{key}"

            # Increment counter and set expiry
            current = await redis.incr(full_key)
            if current == 1:
                await redis.expire(full_key, window_seconds)

            if current > max_requests:
                ttl = await redis.ttl(full_key)
                logger.warning(f"Rate limit exceeded for {key}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many requests. Try again in {ttl} seconds.",
                )
        except HTTPException:
            raise
        except RedisError as e:
            logger.error(f"Redis connection error - rate limiter unavailable: {type(e).__name__}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate limiter unavailable",
            )

        return True

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Singleton
_auth_rate_limiter: Optional[AuthRateLimiter] = None


def get_auth_rate_limiter() -> AuthRateLimiter:
    """Get the auth rate limiter singleton."""
    global _auth_rate_limiter
    settings = get_settings()
    if _auth_rate_limiter is None:
        if not settings.redis_url:
            raise RuntimeError("REDIS_URL not configured - rate limiter requires Redis")
        _auth_rate_limiter = AuthRateLimiter(settings.redis_url)
    return _auth_rate_limiter


# FastAPI dependencies for rate limiting
async def rate_limit_forgot_password(request: Request):
    """Rate limit dependency for forgot-password endpoint (3 requests per 15 minutes)."""
    # Skip rate limiting for OPTIONS (CORS preflight)
    if request.method == "OPTIONS":
        return
    limiter = get_auth_rate_limiter()
    client_ip = request.client.host if request.client else "unknown"
    await limiter.check_rate_limit(
        key=f"forgot_password:{client_ip}",
        max_requests=3,
        window_seconds=900,  # 15 minutes
    )


async def rate_limit_request_verify(request: Request):
    """Rate limit dependency for request-verify-token endpoint (3 requests per 15 minutes)."""
    # Skip rate limiting for OPTIONS (CORS preflight)
    if request.method == "OPTIONS":
        return
    limiter = get_auth_rate_limiter()
    client_ip = request.client.host if request.client else "unknown"
    await limiter.check_rate_limit(
        key=f"request_verify:{client_ip}",
        max_requests=3,
        window_seconds=900,  # 15 minutes
    )


async def rate_limit_register(request: Request):
    """Rate limit dependency for register endpoint (5 requests per hour)."""
    # Skip rate limiting for OPTIONS (CORS preflight)
    if request.method == "OPTIONS":
        return
    limiter = get_auth_rate_limiter()
    client_ip = request.client.host if request.client else "unknown"
    await limiter.check_rate_limit(
        key=f"register:{client_ip}",
        max_requests=5,
        window_seconds=3600,  # 1 hour
    )


async def rate_limit_login(request: Request):
    """Rate limit dependency for login endpoint (5 requests per 15 minutes)."""
    # Skip rate limiting for OPTIONS (CORS preflight)
    if request.method == "OPTIONS":
        return
    limiter = get_auth_rate_limiter()
    client_ip = request.client.host if request.client else "unknown"
    await limiter.check_rate_limit(
        key=f"login:{client_ip}",
        max_requests=5,
        window_seconds=900,  # 15 minutes
    )
