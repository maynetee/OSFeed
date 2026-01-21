from __future__ import annotations

import asyncio
from typing import Awaitable, Optional, TypeVar

from app.config import get_settings

T = TypeVar("T")
settings = get_settings()

_translation_semaphore: Optional[asyncio.Semaphore] = None
_translation_lock = asyncio.Lock()


async def _get_translation_semaphore() -> asyncio.Semaphore:
    """Initialize the translation semaphore lazily."""
    global _translation_semaphore
    async with _translation_lock:
        if _translation_semaphore is None:
            _translation_semaphore = asyncio.Semaphore(settings.translation_concurrency)
        return _translation_semaphore


async def run_translation(awaitable: Awaitable[T]) -> T:
    """Run a translation task within the shared translation pool."""
    semaphore = await _get_translation_semaphore()
    async with semaphore:
        return await awaitable
