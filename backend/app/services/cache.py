from __future__ import annotations

from typing import Optional

from redis.asyncio import Redis

from app.config import get_settings

_redis_client: Optional[Redis] = None


def get_redis_client() -> Optional[Redis]:
    settings = get_settings()
    if not settings.redis_url:
        return None

    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis_client
