"""Translation Pool - Concurrency Control for Translation Tasks

This module provides a shared semaphore-based pool to limit concurrent
translation API calls. It prevents overwhelming the LLM provider with too
many simultaneous requests while allowing controlled parallel processing.

The pool is initialized lazily on first use and shared across all translation
tasks. Concurrency limit is configured via settings.translation_concurrency.

Key components:
- Shared semaphore for rate limiting translation tasks
- Lazy initialization with thread-safe creation
- Generic async wrapper for translation tasks
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Optional, TypeVar

from app.config import get_settings

T = TypeVar("T")
settings = get_settings()

# Global semaphore shared across all translation tasks
_translation_semaphore: Optional[asyncio.Semaphore] = None
# Lock to ensure thread-safe semaphore initialization
_translation_lock = asyncio.Lock()


async def _get_translation_semaphore() -> asyncio.Semaphore:
    """Initialize the translation semaphore lazily with thread-safe creation.

    This function ensures the global translation semaphore is created exactly once,
    even when called concurrently from multiple tasks. Uses a lock to prevent
    race conditions during initialization.

    The semaphore limit is read from settings.translation_concurrency, which
    controls how many translation API calls can run simultaneously.

    Returns:
        asyncio.Semaphore: The shared semaphore for translation concurrency control
    """
    global _translation_semaphore
    async with _translation_lock:
        if _translation_semaphore is None:
            _translation_semaphore = asyncio.Semaphore(settings.translation_concurrency)
        return _translation_semaphore


async def run_translation(awaitable: Awaitable[T]) -> T:
    """Run a translation task within the shared translation pool.

    This function wraps any translation-related async operation to ensure it
    respects the global concurrency limit. It acquires a slot from the shared
    semaphore before executing the task, automatically releasing it when done.

    Use this wrapper for all LLM translation API calls to prevent:
    - Overwhelming the LLM provider with too many simultaneous requests
    - Hitting rate limits from the translation service
    - Excessive resource consumption from unlimited parallel translations

    The awaitable is executed only when a semaphore slot is available. If the
    pool is at capacity, this function will wait until a slot becomes available.

    Args:
        awaitable: The async translation task to execute (typically a translator API call)

    Returns:
        The result of the awaitable (generic type T preserved)

    Example:
        result = await run_translation(translator.translate_text(text, target_lang))
    """
    semaphore = await _get_translation_semaphore()
    async with semaphore:
        return await awaitable
