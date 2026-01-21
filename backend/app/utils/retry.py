"""Retry utilities for handling Telegram rate limiting (Flood Waits).

This module provides decorators and utilities for handling Telegram API rate limiting,
implementing exponential backoff with jitter to avoid "thundering herd" problems.
"""
import asyncio
import random
import logging
from functools import wraps
from typing import Callable, TypeVar, Any

from telethon.errors import (
    FloodWaitError,
    SlowModeWaitError,
    ServerError,
    TimedOutError,
)

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Type variable for generic decorator
F = TypeVar("F", bound=Callable[..., Any])

# Global semaphore for rate limiting concurrent channel fetches
_channel_semaphore: asyncio.Semaphore | None = None
_channel_semaphore_lock: asyncio.Lock | None = None


def _get_lock() -> asyncio.Lock:
    """Get or create the initialization lock (must be called from async context)."""
    global _channel_semaphore_lock
    if _channel_semaphore_lock is None:
        _channel_semaphore_lock = asyncio.Lock()
    return _channel_semaphore_lock


async def get_channel_semaphore() -> asyncio.Semaphore:
    """Get or create the global channel semaphore for rate limiting.
    
    Thread-safe initialization using async lock to prevent race conditions.
    """
    global _channel_semaphore
    if _channel_semaphore is None:
        async with _get_lock():
            # Double-check after acquiring lock
            if _channel_semaphore is None:
                _channel_semaphore = asyncio.Semaphore(settings.telegram_concurrent_channels)
    return _channel_semaphore


def telegram_retry(func: F) -> F:
    """Decorator for handling Telegram Flood Waits with exponential backoff.

    This decorator wraps async functions that interact with the Telegram API,
    automatically handling rate limiting errors (FloodWaitError) and other
    transient errors with exponential backoff.

    The decorator respects the following settings:
    - telegram_max_retries: Maximum number of retry attempts
    - telegram_base_delay: Base delay between retries (in seconds)
    - telegram_max_delay: Maximum delay between retries (in seconds)
    - telegram_jitter: Whether to add random jitter to delays

    Example:
        @telegram_retry
        async def fetch_messages(channel_id: int) -> list:
            return await client.get_messages(channel_id, limit=100)
    """

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        max_retries = settings.telegram_max_retries
        base_delay = settings.telegram_base_delay
        max_delay = settings.telegram_max_delay
        use_jitter = settings.telegram_jitter

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)

            except FloodWaitError as e:
                # Telegram tells us exactly how long to wait
                wait_time = e.seconds
                # Add jitter to avoid all clients retrying at the same time
                jitter = 0.0
                if use_jitter:
                    jitter = random.uniform(1, 5)
                    wait_time += jitter

                logger.warning(
                    f"FloodWaitError: Telegram requires waiting {e.seconds}s "
                    f"(+{jitter:.1f}s jitter). Attempt {attempt + 1}/{max_retries + 1} "
                    f"for {func.__name__}"
                )

                if attempt < max_retries:
                    await asyncio.sleep(wait_time)
                    last_exception = e
                else:
                    logger.error(
                        f"Max retries exceeded for {func.__name__} after FloodWaitError"
                    )
                    raise

            except SlowModeWaitError as e:
                # Channel has slow mode enabled
                wait_time = e.seconds
                logger.warning(
                    f"SlowModeWaitError: Channel requires waiting {wait_time}s. "
                    f"Attempt {attempt + 1}/{max_retries + 1} for {func.__name__}"
                )

                if attempt < max_retries:
                    await asyncio.sleep(wait_time)
                    last_exception = e
                else:
                    raise

            except (ServerError, TimedOutError, ConnectionError, OSError) as e:
                # Transient errors - use exponential backoff
                delay = min(base_delay * (2 ** attempt), max_delay)

                if use_jitter:
                    # Add random jitter between 0.5x and 1.5x the delay
                    delay *= random.uniform(0.5, 1.5)

                logger.warning(
                    f"Transient error in {func.__name__}: {type(e).__name__}: {e}. "
                    f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries + 1})"
                )

                if attempt < max_retries:
                    await asyncio.sleep(delay)
                    last_exception = e
                else:
                    logger.error(
                        f"Max retries exceeded for {func.__name__}: {type(e).__name__}: {e}"
                    )
                    raise

            except Exception as e:
                # Non-retryable error - log and re-raise immediately
                logger.error(
                    f"Non-retryable error in {func.__name__}: {type(e).__name__}: {e}"
                )
                raise

        # This should never be reached, but just in case
        if last_exception:
            raise last_exception

        return None

    return wrapper  # type: ignore


async def with_rate_limit(coro):
    """Execute a coroutine with global rate limiting.

    This function ensures that no more than `telegram_concurrent_channels`
    coroutines are executing simultaneously, preventing overwhelming the
    Telegram API with too many concurrent requests.

    Example:
        results = await asyncio.gather(*[
            with_rate_limit(fetch_channel(ch)) for ch in channels
        ])
    """
    semaphore = await get_channel_semaphore()
    async with semaphore:
        return await coro


async def collect_with_rate_limit(channels: list, fetch_func: Callable) -> list:
    """Collect data from multiple channels with rate limiting.

    This function fetches data from multiple channels concurrently while
    respecting the configured concurrency limit. It handles exceptions
    gracefully, logging errors for failed channels.

    Args:
        channels: List of channel objects to fetch from
        fetch_func: Async function that takes a channel and returns data

    Returns:
        List of results (or None for failed channels)

    Example:
        async def fetch_messages(channel):
            return await collector.get_recent_messages(channel.telegram_id)

        results = await collect_with_rate_limit(channels, fetch_messages)
    """
    async def fetch_with_limit(channel):
        try:
            return await with_rate_limit(fetch_func(channel))
        except Exception as e:
            logger.error(
                f"Failed to fetch from channel {getattr(channel, 'username', channel)}: "
                f"{type(e).__name__}: {e}"
            )
            return None

    tasks = [fetch_with_limit(ch) for ch in channels]
    return await asyncio.gather(*tasks, return_exceptions=False)
