"""Message collection job - Telegram functionality removed.

This job previously collected messages from Telegram channels.
Collection is now disabled until a new data source is configured.
The deduplication logic is preserved for existing messages.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func

from app.models.message import Message
from app.services.deduplicator import deduplicator
from app.database import AsyncSessionLocal


logger = logging.getLogger(__name__)

# Lock for cross-channel deduplication synchronization
_dedup_lock = asyncio.Lock()

# Chunk size for loading messages during deduplication to bound memory usage
DEDUP_CHUNK_SIZE = 500


async def collect_messages_job() -> None:
    """Background job - message collection disabled.
    
    Telegram integration has been removed. This job now only logs
    that collection is disabled. The deduplication logic is preserved
    and can be triggered manually if needed.
    """
    logger.info("Message collection job skipped - Telegram integration removed")


async def _run_chunked_deduplication() -> None:
    """Run cross-channel deduplication in chunks.
    
    This function is preserved for manual deduplication of existing messages.
    """
    async with _dedup_lock:
        logger.info("Running cross-channel deduplication (with lock)...")
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

        async with AsyncSessionLocal() as db:
            count_result = await db.execute(
                select(func.count(Message.id))
                .where(Message.published_at >= cutoff_time)
            )
            total_count = count_result.scalar() or 0

        if total_count == 0:
            logger.info("No recent messages to deduplicate")
            return

        logger.info(f"Deduplicating {total_count} messages in chunks of {DEDUP_CHUNK_SIZE}")

        processed = 0
        offset = 0

        while offset < total_count:
            async with AsyncSessionLocal() as db:
                chunk_result = await db.execute(
                    select(Message)
                    .where(Message.published_at >= cutoff_time)
                    .order_by(Message.published_at.desc())
                    .offset(offset)
                    .limit(DEDUP_CHUNK_SIZE)
                )
                chunk_messages = list(chunk_result.scalars().all())

                if not chunk_messages:
                    break

                await deduplicator.mark_duplicates(chunk_messages, cutoff_time=cutoff_time)
                await db.commit()

                processed += len(chunk_messages)
                logger.debug(f"Deduplication progress: {processed}/{total_count}")

            offset += DEDUP_CHUNK_SIZE

        logger.info(f"Deduplication completed for {processed} messages")
