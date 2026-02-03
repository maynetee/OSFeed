"""Generic retry utilities with exponential backoff.

This module provides decorators and utilities for handling transient errors
with exponential backoff and jitter.
"""
import asyncio
import random
import logging
from functools import wraps
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)

# Type variable for generic decorator
F = TypeVar("F", bound=Callable[..., Any])


def async_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    use_jitter: bool = True,
    retryable_exceptions: tuple = (ConnectionError, TimeoutError, OSError),
):
    """Decorator for handling transient errors with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries (in seconds)
        max_delay: Maximum delay between retries (in seconds)
        use_jitter: Whether to add random jitter to delays
        retryable_exceptions: Tuple of exception types to retry on

    Example:
        @async_retry(max_retries=3)
        async def fetch_data(url: str) -> dict:
            return await client.get(url)
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except retryable_exceptions as e:
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
                    # Intentional catch-all for non-retryable errors (anything not in retryable_exceptions)
                    # Log the error type for debugging, then re-raise immediately to fail fast
                    logger.error(
                        f"Non-retryable error in {func.__name__}: {type(e).__name__}: {e}"
                    )
                    raise

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception

            return None

        return wrapper  # type: ignore
    return decorator


async def with_semaphore(coro, semaphore: asyncio.Semaphore):
    """Execute a coroutine with a semaphore for rate limiting.

    Example:
        sem = asyncio.Semaphore(10)
        results = await asyncio.gather(*[
            with_semaphore(fetch(url), sem) for url in urls
        ])
    """
    async with semaphore:
        return await coro
