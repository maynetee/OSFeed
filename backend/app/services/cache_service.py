"""Generic Redis Cache Service.

Provides a clean abstraction over Redis cache operations, encapsulating
the common boilerplate: get client, check for None, try/except, log failures.
"""

import logging
from typing import Optional, Any

from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from redis.exceptions import ConnectionError, TimeoutError

from app.config import get_settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis cache service with automatic error handling and fallbacks.

    All methods gracefully degrade when Redis is unavailable:
    - get() returns None
    - set()/setex()/delete() silently fail
    - incr() returns 0

    This allows cache operations to fail without breaking application logic.
    """

    def __init__(self):
        self._redis: Optional[Redis] = None

    async def _get_redis(self) -> Optional[Redis]:
        """Get or create Redis connection.

        Returns None if Redis URL is not configured.
        Uses retry logic with exponential backoff for transient failures.
        """
        settings = get_settings()
        if not settings.redis_url:
            return None

        if self._redis is None:
            retry = Retry(ExponentialBackoff(), retries=3)
            self._redis = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                retry=retry,
                retry_on_error=[ConnectionError, TimeoutError],
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            logger.info("Redis cache client initialized with retry logic")
        return self._redis

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value as string, or None if not found or on error
        """
        client = await self._get_redis()
        if client is None:
            return None
        try:
            return await client.get(key)
        except Exception as e:
            logger.debug(f"Failed to get cache key '{key}': {e}")
            return None

    async def set(self, key: str, value: Any) -> bool:
        """Set value in cache without expiration.

        Args:
            key: Cache key
            value: Value to cache (will be converted to string)

        Returns:
            True if successful, False on error
        """
        client = await self._get_redis()
        if client is None:
            return False
        try:
            await client.set(key, value)
            return True
        except Exception as e:
            logger.debug(f"Failed to set cache key '{key}': {e}")
            return False

    async def setex(self, key: str, ttl: int, value: Any) -> bool:
        """Set value in cache with expiration time.

        Args:
            key: Cache key
            ttl: Time-to-live in seconds
            value: Value to cache (will be converted to string)

        Returns:
            True if successful, False on error
        """
        client = await self._get_redis()
        if client is None:
            return False
        try:
            await client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.debug(f"Failed to setex cache key '{key}' with TTL {ttl}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False on error
        """
        client = await self._get_redis()
        if client is None:
            return False
        try:
            await client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Failed to delete cache key '{key}': {e}")
            return False

    async def incr(self, key: str) -> int:
        """Increment counter in cache.

        Args:
            key: Cache key for counter

        Returns:
            New counter value, or 0 on error
        """
        client = await self._get_redis()
        if client is None:
            return 0
        try:
            return await client.incr(key)
        except Exception as e:
            logger.debug(f"Failed to increment cache key '{key}': {e}")
            return 0


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get the singleton cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
