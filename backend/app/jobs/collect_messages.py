"""Message collection job for Telegram channels.

This job runs periodically to:
1. Sync messages from all active channels
2. Run deduplication on new messages
3. Trigger translation for untranslated messages
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import select, func, and_

from app.models.message import Message
from app.models.channel import Channel
from app.services.deduplicator import deduplicator
from app.services.telegram_client import get_telegram_client
from app.services.fetch_queue import enqueue_fetch_job
from app.database import AsyncSessionLocal
from app.config import settings

logger = logging.getLogger(__name__)

# Lock for cross-channel deduplication synchronization
_dedup_lock = asyncio.Lock()

# Chunk size for loading messages during deduplication to bound memory usage
DEDUP_CHUNK_SIZE = 500


async def collect_messages_job() -> None:
    """Background job to collect messages from all active Telegram channels.

    This job:
    1. Gets all active channels
    2. Enqueues fetch jobs for channels that need syncing
    3. Runs deduplication after collection

    Runs every 5 minutes via scheduler.
    """
    logger.info("Starting message collection job")

    try:
        # Get all active channels
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Channel).where(Channel.is_active == True)
            )
            channels = result.scalars().all()

        if not channels:
            logger.info("No active channels to collect from")
            return

        logger.info(f"Found {len(channels)} active channels")

        # Check which channels need syncing (haven't been synced recently)
        sync_interval = timedelta(seconds=settings.telegram_sync_interval_seconds)
        now = datetime.now(timezone.utc)

        channels_to_sync = []
        for channel in channels:
            if channel.last_fetched_at is None:
                channels_to_sync.append(channel)
            elif (now - channel.last_fetched_at) > sync_interval:
                channels_to_sync.append(channel)

        if not channels_to_sync:
            logger.info("All channels are up to date")
        else:
            logger.info(f"Syncing {len(channels_to_sync)} channels")

            # Enqueue fetch jobs (fetch_queue handles rate limiting and deduplication)
            for channel in channels_to_sync:
                try:
                    await enqueue_fetch_job(
                        channel.id,
                        channel.username,
                        days=1  # Only fetch last day for incremental sync
                    )
                except Exception as e:
                    logger.error(f"Failed to enqueue fetch for {channel.username}: {e}")

        # Run deduplication on recent messages
        await _run_chunked_deduplication()

        logger.info("Message collection job completed")

    except Exception as e:
        logger.exception(f"Message collection job failed: {e}")


async def collect_channel_messages(channel: Channel, days: int = 7) -> int:
    """Fetch messages from a specific Telegram channel.

    This is called by fetch_queue workers.

    Args:
        channel: Channel model instance
        days: Number of days of history to fetch

    Returns:
        Number of new messages collected
    """
    logger.info(f"Collecting messages from {channel.username}")

    telegram_client = get_telegram_client()
    new_messages = 0

    # Get last known message ID for incremental sync
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(func.max(Message.telegram_message_id))
            .where(Message.channel_id == channel.id)
        )
        last_msg_id = result.scalar() or 0

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    batch_size = settings.telegram_batch_size

    try:
        # Fetch messages in batches
        offset_date = None

        while True:
            messages = await telegram_client.get_messages(
                channel.username,
                limit=batch_size,
                min_id=last_msg_id,
                offset_date=offset_date
            )

            if not messages:
                break

            # Process batch
            async with AsyncSessionLocal() as db:
                for msg in messages:
                    # Skip if too old
                    msg_date = msg.date.replace(tzinfo=timezone.utc) if msg.date else None
                    if msg_date and msg_date < cutoff_date:
                        continue

                    # Skip if already exists
                    existing = await db.execute(
                        select(Message).where(
                            and_(
                                Message.channel_id == channel.id,
                                Message.telegram_message_id == msg.id
                            )
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue

                    # Create new message
                    new_msg = await _process_telegram_message(msg, channel)
                    db.add(new_msg)
                    new_messages += 1

                await db.commit()

            # Check if we've reached the cutoff
            if messages[-1].date:
                oldest = messages[-1].date.replace(tzinfo=timezone.utc)
                if oldest < cutoff_date:
                    break
                offset_date = messages[-1].date
            else:
                break

        # Update channel last_fetched_at
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Channel).where(Channel.id == channel.id)
            )
            ch = result.scalar_one()
            ch.last_fetched_at = datetime.now(timezone.utc)
            await db.commit()

        logger.info(f"Collected {new_messages} new messages from {channel.username}")
        return new_messages

    except Exception as e:
        logger.exception(f"Error collecting from {channel.username}: {e}")
        return new_messages


async def _process_telegram_message(tg_msg, channel: Channel) -> Message:
    """Convert a Telethon message to an OSFeed Message model.

    Args:
        tg_msg: Telethon message object
        channel: Channel model instance

    Returns:
        Message model instance (not yet added to session)
    """
    # Determine media type
    media_type = None
    media_urls = []

    if tg_msg.photo:
        media_type = "photo"
    elif tg_msg.video:
        media_type = "video"
    elif tg_msg.document:
        media_type = "document"
    elif tg_msg.audio:
        media_type = "audio"

    # Get message text
    text = tg_msg.text or tg_msg.message or ""

    # Determine if translation is needed
    needs_translation = bool(text.strip())

    # Get published date
    published_at = datetime.now(timezone.utc)
    if tg_msg.date:
        published_at = tg_msg.date.replace(tzinfo=timezone.utc)

    return Message(
        channel_id=channel.id,
        telegram_message_id=tg_msg.id,
        original_text=text,
        media_type=media_type,
        media_urls=media_urls,
        published_at=published_at,
        fetched_at=datetime.now(timezone.utc),
        needs_translation=needs_translation,
        is_duplicate=False,
        originality_score=100
    )


async def _run_chunked_deduplication() -> None:
    """Run cross-channel deduplication in chunks.

    This function processes recent messages to identify duplicates
    using vector similarity matching.
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
