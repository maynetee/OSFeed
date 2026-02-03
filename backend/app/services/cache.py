from __future__ import annotations

import logging
from typing import Optional

from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from redis.exceptions import ConnectionError, TimeoutError

from app.config import get_settings
from app.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)

_redis_client: Optional[Redis] = None


def get_redis_client() -> Optional[Redis]:
    settings = get_settings()
    if not settings.redis_url:
        return None

    global _redis_client
    if _redis_client is None:
        retry = Retry(ExponentialBackoff(), retries=3)
        _redis_client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            retry=retry,
            retry_on_error=[ConnectionError, TimeoutError],
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        logger.info("Redis client initialized with retry logic")
    return _redis_client


# Translation cache hit/miss tracking keys
TRANSLATION_CACHE_HITS_KEY = "stats:translation:cache_hits"
TRANSLATION_CACHE_MISSES_KEY = "stats:translation:cache_misses"


async def increment_translation_cache_hit() -> None:
    """Increment the global translation cache hit counter in Redis."""
    cache = get_cache_service()
    await cache.incr(TRANSLATION_CACHE_HITS_KEY)


async def increment_translation_cache_miss() -> None:
    """Increment the global translation cache miss counter in Redis."""
    cache = get_cache_service()
    await cache.incr(TRANSLATION_CACHE_MISSES_KEY)


async def get_translation_cache_stats() -> dict:
    """Read translation cache hit/miss counters from Redis."""
    cache = get_cache_service()
    hits_str = await cache.get(TRANSLATION_CACHE_HITS_KEY)
    misses_str = await cache.get(TRANSLATION_CACHE_MISSES_KEY)

    hits = int(hits_str) if hits_str else 0
    misses = int(misses_str) if misses_str else 0
    total = hits + misses
    hit_rate = (hits / total * 100) if total > 0 else 0.0

    return {"cache_hits": hits, "cache_misses": misses, "cache_hit_rate": round(hit_rate, 2)}
