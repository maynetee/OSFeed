"""Channel Join Queue Service.

Manages a queue for channel joins when the daily Telegram limit is reached.
Queued channels are processed at midnight UTC when the limit resets.

Redis key: telegram:join_queue
Format: JSON list of {username, user_id, queued_at}
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID
from redis.asyncio import Redis

from app.config import settings
from app.database import AsyncSessionLocal
from app.services.telegram_client import get_telegram_client

logger = logging.getLogger(__name__)

QUEUE_KEY = "telegram:join_queue"


async def _get_redis() -> Redis:
    """Get Redis connection."""
    if not settings.redis_url:
        raise RuntimeError("REDIS_URL not configured")
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def queue_channel_join(username: str, user_id: UUID) -> int:
    """Add a channel to the join queue.

    Args:
        username: Channel username to join
        user_id: User who requested the join

    Returns:
        Position in queue (1-indexed)
    """
    redis = await _get_redis()

    # Check for duplicates
    existing = await redis.lrange(QUEUE_KEY, 0, -1)
    for item in existing:
        data = json.loads(item)
        if data["username"].lower() == username.lower():
            # Already in queue, find position
            for i, item in enumerate(existing):
                if json.loads(item)["username"].lower() == username.lower():
                    logger.info(f"Channel {username} already in queue at position {i + 1}")
                    return i + 1

    # Add to queue
    entry = {
        "username": username,
        "user_id": str(user_id),
        "queued_at": datetime.now(timezone.utc).isoformat()
    }

    await redis.rpush(QUEUE_KEY, json.dumps(entry))
    position = await redis.llen(QUEUE_KEY)

    logger.info(f"Queued channel {username} for user {user_id}, position: {position}")
    return position


async def get_queue_position(username: str) -> Optional[int]:
    """Get position of a channel in the queue.

    Args:
        username: Channel username to look up

    Returns:
        Position (1-indexed) or None if not in queue
    """
    redis = await _get_redis()
    existing = await redis.lrange(QUEUE_KEY, 0, -1)

    for i, item in enumerate(existing):
        data = json.loads(item)
        if data["username"].lower() == username.lower():
            return i + 1

    return None


async def get_queue_length() -> int:
    """Get current queue length."""
    redis = await _get_redis()
    return await redis.llen(QUEUE_KEY)


async def get_queue_entries() -> List[Dict[str, Any]]:
    """Get all entries in the queue."""
    redis = await _get_redis()
    entries = await redis.lrange(QUEUE_KEY, 0, -1)
    return [json.loads(e) for e in entries]


async def process_join_queue() -> int:
    """Process queued channel joins.

    Called by scheduler at midnight UTC when the daily limit resets.
    Processes up to the daily limit of channels.

    Returns:
        Number of channels successfully joined
    """
    redis = await _get_redis()
    telegram_client = get_telegram_client()

    daily_limit = settings.telegram_join_channel_daily_limit
    processed = 0
    failed = 0

    logger.info(f"Processing join queue (limit: {daily_limit})")

    while processed < daily_limit:
        # Pop from front of queue
        entry_json = await redis.lpop(QUEUE_KEY)
        if not entry_json:
            break  # Queue empty

        entry = json.loads(entry_json)
        username = entry["username"]
        user_id = entry["user_id"]

        try:
            # Check if we can still join
            if not await telegram_client.can_join_channel():
                # Put back at front of queue and stop
                await redis.lpush(QUEUE_KEY, entry_json)
                logger.warning("Daily join limit reached during queue processing")
                break

            # Resolve and join the channel
            channel_info = await telegram_client.resolve_channel(username)
            await telegram_client.join_public_channel(username)
            await telegram_client.record_channel_join()

            # Create channel in database
            async with AsyncSessionLocal() as db:
                from app.models.channel import Channel, user_channels
                from sqlalchemy import select, insert

                # Check if channel was created while queued
                result = await db.execute(
                    select(Channel).where(Channel.username == username)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    # Link user to existing channel
                    await db.execute(
                        insert(user_channels).values(
                            user_id=UUID(user_id),
                            channel_id=existing.id
                        ).prefix_with("OR IGNORE")
                    )
                else:
                    # Create new channel
                    channel = Channel(
                        username=username,
                        telegram_id=channel_info['telegram_id'],
                        title=channel_info['title'],
                        description=channel_info.get('description'),
                        is_active=True
                    )
                    db.add(channel)
                    await db.flush()

                    # Link user
                    await db.execute(
                        insert(user_channels).values(
                            user_id=UUID(user_id),
                            channel_id=channel.id
                        )
                    )

                await db.commit()

            processed += 1
            logger.info(f"Processed queued channel: {username} for user {user_id}")

        except Exception as e:
            failed += 1
            logger.error(f"Failed to process queued channel {username}: {e}")
            # Don't re-queue failed entries to avoid infinite loops

    remaining = await redis.llen(QUEUE_KEY)
    logger.info(
        f"Queue processing complete: {processed} joined, {failed} failed, {remaining} remaining"
    )

    return processed


async def remove_from_queue(username: str) -> bool:
    """Remove a channel from the queue.

    Args:
        username: Channel username to remove

    Returns:
        True if removed, False if not found
    """
    redis = await _get_redis()
    entries = await redis.lrange(QUEUE_KEY, 0, -1)

    for entry in entries:
        data = json.loads(entry)
        if data["username"].lower() == username.lower():
            await redis.lrem(QUEUE_KEY, 1, entry)
            logger.info(f"Removed {username} from join queue")
            return True

    return False
