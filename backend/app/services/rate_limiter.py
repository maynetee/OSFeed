"""Redis Token Bucket Rate Limiter for Telegram API.

Provides coordinated rate limiting across multiple workers using Redis
for atomic token bucket operations.
"""
import asyncio
import time
import logging
from datetime import datetime, timezone
from typing import Tuple, Optional
from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisTokenBucket:
    """Token bucket rate limiter backed by Redis.

    Algorithm:
    - Store {tokens: float, last_refill: timestamp} in Redis hash
    - On acquire: refill tokens based on time elapsed, consume requested amount
    - If tokens < requested: return wait time, don't consume

    Uses Redis MULTI/EXEC for atomic operations across workers.
    """

    RATE_LIMIT_KEY = "telegram:rate_limit"
    JOIN_COUNT_KEY_PREFIX = "telegram:join_count"

    def __init__(
        self,
        redis_url: str,
        tokens_per_minute: int = 30,
        max_tokens: int = 60
    ):
        self.redis_url = redis_url
        self.tokens_per_minute = tokens_per_minute
        self.max_tokens = max_tokens
        self.tokens_per_second = tokens_per_minute / 60.0
        self._redis: Optional[Redis] = None

    async def _get_redis(self) -> Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = Redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def acquire(self, tokens: int = 1) -> Tuple[bool, float]:
        """Try to acquire tokens from the bucket.

        Returns:
            Tuple of (success, wait_seconds):
            - If success=True: tokens consumed, proceed immediately
            - If success=False: wait wait_seconds before retrying
        """
        redis = await self._get_redis()
        now = time.time()

        # Use Lua script for atomic check-and-update
        lua_script = """
        local key = KEYS[1]
        local tokens_requested = tonumber(ARGV[1])
        local max_tokens = tonumber(ARGV[2])
        local refill_rate = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])

        -- Get current state
        local current_tokens = tonumber(redis.call('HGET', key, 'tokens') or max_tokens)
        local last_refill = tonumber(redis.call('HGET', key, 'last_refill') or now)

        -- Calculate refill
        local elapsed = now - last_refill
        local refilled = current_tokens + (elapsed * refill_rate)
        if refilled > max_tokens then
            refilled = max_tokens
        end

        -- Check if we have enough tokens
        if refilled >= tokens_requested then
            -- Consume tokens
            local new_tokens = refilled - tokens_requested
            redis.call('HSET', key, 'tokens', new_tokens)
            redis.call('HSET', key, 'last_refill', now)
            return {1, 0}  -- success, no wait
        else
            -- Not enough tokens, calculate wait time
            local needed = tokens_requested - refilled
            local wait = needed / refill_rate
            -- Update state anyway to track time
            redis.call('HSET', key, 'tokens', refilled)
            redis.call('HSET', key, 'last_refill', now)
            return {0, wait}  -- fail, wait time
        end
        """

        result = await redis.eval(
            lua_script,
            1,
            self.RATE_LIMIT_KEY,
            tokens,
            self.max_tokens,
            self.tokens_per_second,
            now
        )

        success = bool(result[0])
        wait_seconds = float(result[1])

        if not success:
            logger.debug(f"Rate limit: need to wait {wait_seconds:.2f}s")

        return success, wait_seconds

    async def acquire_with_wait(self, tokens: int = 1, max_wait: float = 60.0) -> bool:
        """Acquire tokens, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire
            max_wait: Maximum seconds to wait

        Returns:
            True if tokens acquired, False if max_wait exceeded
        """
        total_waited = 0.0

        while total_waited < max_wait:
            success, wait_seconds = await self.acquire(tokens)
            if success:
                return True

            if total_waited + wait_seconds > max_wait:
                return False

            await asyncio.sleep(wait_seconds)
            total_waited += wait_seconds

        return False

    def _get_join_count_key(self) -> str:
        """Get Redis key for today's join count."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"{self.JOIN_COUNT_KEY_PREFIX}:{today}"

    async def get_join_count(self) -> int:
        """Get today's JoinChannel count."""
        redis = await self._get_redis()
        key = self._get_join_count_key()
        count = await redis.get(key)
        return int(count) if count else 0

    async def increment_join_count(self) -> int:
        """Increment and return today's JoinChannel count.

        Key auto-expires at midnight UTC (24 hours from creation).
        """
        redis = await self._get_redis()
        key = self._get_join_count_key()

        # Increment and set expiry
        pipe = redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, 86400)  # 24 hours
        results = await pipe.execute()

        new_count = results[0]
        logger.info(f"JoinChannel count for today: {new_count}")
        return new_count

    async def can_join_channel(self, daily_limit: int) -> bool:
        """Check if we can join another channel today."""
        current_count = await self.get_join_count()
        return current_count < daily_limit


# Singleton instance
_rate_limiter: Optional[RedisTokenBucket] = None


def get_rate_limiter() -> RedisTokenBucket:
    """Get the singleton rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        if not settings.redis_url:
            raise RuntimeError("REDIS_URL not configured - rate limiter requires Redis")
        _rate_limiter = RedisTokenBucket(
            redis_url=settings.redis_url,
            tokens_per_minute=settings.telegram_requests_per_minute,
            max_tokens=settings.telegram_requests_per_minute * 2  # 2 minute burst
        )
    return _rate_limiter


async def cleanup_rate_limiter() -> None:
    """Cleanup rate limiter on shutdown."""
    global _rate_limiter
    if _rate_limiter:
        await _rate_limiter.close()
        _rate_limiter = None
