import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from sqlalchemy import select, func

from app.models.channel import Channel
from app.models.message import Message
from app.services.message_bulk import bulk_insert_messages
from app.services.telegram_collector import get_shared_collector
from app.services.deduplicator import deduplicator
from app.database import AsyncSessionLocal
from app.config import get_settings
from app.jobs.translate_pending_messages import translate_pending_messages_job


logger = logging.getLogger(__name__)
settings = get_settings()

# Lock for cross-channel deduplication synchronization
_dedup_lock = asyncio.Lock()

# Chunk size for loading messages during deduplication to bound memory usage
DEDUP_CHUNK_SIZE = 500


async def collect_messages_job() -> None:
    """
    Background job to collect messages from all followed channels.

    IMPORTANT: This job releases the database lock during slow I/O operations
    (Telegram API calls, translation) to prevent blocking other database operations.
    """
    now = datetime.now(timezone.utc)
    logger.info(f"[{now.isoformat()}] Starting message collection job...")

    # Step 1: Get all channels (short DB session)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Channel))
        channels = result.scalars().all()
        # Extract channel data before closing session
        channel_data: List[Tuple[str, str]] = [(c.id, c.username) for c in channels]

    if not channel_data:
        logger.info("No channels to collect from")
        return

    collector = await get_shared_collector()
    total_new_messages = 0
    total_lock = asyncio.Lock()
    fetch_semaphore = asyncio.Semaphore(settings.fetch_workers)

    async def _collect_channel(channel_id: str, channel_username: str) -> int:
        """
        Collect messages for a single channel.
        Returns the number of new messages inserted.
        """
        logger.debug(f"Collecting messages from {channel_username}...")

        try:
            # Step 2: Fetch messages from Telegram (NO DB session held)
            async with fetch_semaphore:
                messages = await collector.get_recent_messages(channel_username, limit=20)

            if not messages:
                return 0

            # Step 3: Prepare messages for upsert (no pre-check needed)
            # bulk_insert_messages uses ON CONFLICT DO NOTHING, so duplicates are safely ignored
            fetched_at = datetime.now(timezone.utc)
            pending_messages = [
                {
                    'channel_id': channel_id,
                    'telegram_message_id': msg_data['message_id'],
                    'original_text': msg_data['text'],
                    'translated_text': None,
                    'source_language': None,
                    'target_language': settings.preferred_language,
                    'needs_translation': True,
                    'media_type': msg_data.get('media_type'),
                    'media_urls': msg_data.get('media_urls', []),
                    'published_at': msg_data['date'],
                    'translated_at': None,
                    'fetched_at': fetched_at,
                }
                for msg_data in messages
            ]

            # Step 4: Save messages to DB using upsert pattern (single transaction)
            # ON CONFLICT DO NOTHING ensures no race condition duplicates
            async with AsyncSessionLocal() as db:
                inserted = await bulk_insert_messages(db, pending_messages)

                # Also update channel's last_fetched_at
                result = await db.execute(select(Channel).where(Channel.id == channel_id))
                channel = result.scalar_one_or_none()
                if channel:
                    channel.last_fetched_at = datetime.now(timezone.utc)

                await db.commit()

            if inserted > 0:
                logger.info(f"Added {inserted} new messages from {channel_username}")

            return inserted

        except Exception as e:
            logger.error(f"Error collecting from {channel_username}: {e}", exc_info=True)
            return 0

    # Create tasks for all channels
    tasks = [
        asyncio.create_task(_collect_channel(channel_id, channel_username))
        for channel_id, channel_username in channel_data
    ]

    # Use return_exceptions=True to prevent one failure from canceling others
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results and handle exceptions
    for i, result in enumerate(results):
        channel_username = channel_data[i][1]
        if isinstance(result, Exception):
            logger.error(f"Task failed for channel {channel_username}: {result}", exc_info=result)
        elif isinstance(result, int):
            async with total_lock:
                total_new_messages += result
        else:
            logger.warning(f"Unexpected result type for {channel_username}: {type(result)}")

    # Step 5: Run cross-channel deduplication with synchronization
    if total_new_messages > 0:
        await _run_chunked_deduplication()

    end_time = datetime.now(timezone.utc)
    logger.info(f"[{end_time.isoformat()}] Message collection job completed. Total new: {total_new_messages}")

    # Trigger translation immediately for any new messages
    if total_new_messages > 0:
        logger.info("Triggering immediate translation...")
        await translate_pending_messages_job()


async def _run_chunked_deduplication() -> None:
    """
    Run cross-channel deduplication in chunks to avoid loading all 24h messages into memory.
    Uses a lock to prevent concurrent deduplication runs from corrupting state.
    """
    async with _dedup_lock:
        logger.info("Running cross-channel deduplication (with lock)...")
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

        # First, get the total count to process
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

        # Process in chunks using offset-based pagination
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

                # Mark duplicates for this chunk
                await deduplicator.mark_duplicates(chunk_messages, cutoff_time=cutoff_time)
                await db.commit()

                processed += len(chunk_messages)
                logger.debug(f"Deduplication progress: {processed}/{total_count}")

            offset += DEDUP_CHUNK_SIZE

        logger.info(f"Deduplication completed for {processed} messages")
