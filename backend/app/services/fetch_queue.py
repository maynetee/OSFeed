"""Fetch queue service - Telegram functionality removed.

This module previously managed Telegram message fetching.
It now provides stub functions to prevent import errors.
Message collection is currently disabled.
"""
import asyncio
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

# Stub worker management
_worker_tasks: list = []


async def start_fetch_worker() -> None:
    """Stub - fetch worker disabled (Telegram integration removed)."""
    logger.info("Fetch worker disabled - Telegram integration removed")


async def stop_fetch_worker() -> None:
    """Stub - fetch worker disabled."""
    pass


async def enqueue_fetch_job(channel_id: UUID, username: str, days: int):
    """Stub - fetch jobs disabled.
    
    Returns None to indicate job creation failed.
    """
    logger.warning(
        "Fetch job requested for %s but Telegram integration is disabled",
        username
    )
    return None
