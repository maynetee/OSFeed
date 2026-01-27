from __future__ import annotations

import logging
from typing import Optional

from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from redis.exceptions import ConnectionError, TimeoutError

from app.config import get_settings

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
