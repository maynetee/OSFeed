"""Fetch Queue Service for Telegram message collection.

Manages a Redis-backed job queue for fetching messages from Telegram channels.
Workers process jobs asynchronously while respecting rate limits.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from uuid import UUID
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.fetch_job import FetchJob
from app.models.channel import Channel
from app.models.message import Message

logger = logging.getLogger(__name__)

# Redis keys
FETCH_QUEUE_KEY = "osfeed:fetch_queue"
ACTIVE_JOBS_KEY = "osfeed:active_fetch_jobs"

# Worker state
_worker_tasks: List[asyncio.Task] = []
_shutdown_event: Optional[asyncio.Event] = None


async def _get_redis() -> Redis:
    """Get Redis connection."""
    if not settings.redis_url:
        raise RuntimeError("REDIS_URL not configured")
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def enqueue_fetch_job(
    channel_id: UUID,
    username: str,
    days: int = 7
) -> Optional[FetchJob]:
    """Create a fetch job and add to Redis queue.

    Args:
        channel_id: Channel UUID
        username: Channel username
        days: Number of days of history to fetch

    Returns:
        FetchJob if created, None if duplicate job exists
    """
    redis = await _get_redis()

    # Check for existing active job for this channel
    active_jobs = await redis.smembers(ACTIVE_JOBS_KEY)
    for job_data in active_jobs:
        job = json.loads(job_data)
        if job["channel_id"] == str(channel_id):
            logger.info(f"Fetch job already active for channel {username}")
            return None

    # Create job in database
    async with AsyncSessionLocal() as db:
        job = FetchJob(
            channel_id=channel_id,
            status="queued",
            days=days,
            total_messages=0,
            new_messages=0,
            processed_messages=0
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        # Add to Redis queue
        job_data = {
            "job_id": str(job.id),
            "channel_id": str(channel_id),
            "username": username,
            "days": days,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await redis.rpush(FETCH_QUEUE_KEY, json.dumps(job_data))

        logger.info(f"Enqueued fetch job {job.id} for channel {username}")
        return job


async def _update_job_status(
    job_id: UUID,
    status: str,
    stage: str = None,
    total: int = None,
    new: int = None,
    processed: int = None,
    error: str = None
) -> None:
    """Update job status in database."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        result = await db.execute(
            select(FetchJob).where(FetchJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if job:
            job.status = status
            if stage is not None:
                job.stage = stage
            if total is not None:
                job.total_messages = total
            if new is not None:
                job.new_messages = new
            if processed is not None:
                job.processed_messages = processed
            if error:
                job.error_message = error

            if status == "running" and job.started_at is None:
                job.started_at = datetime.now(timezone.utc)
            if status in ("completed", "failed"):
                job.finished_at = datetime.now(timezone.utc)

            await db.commit()


async def _process_fetch_job(job_data: dict) -> None:
    """Process a single fetch job.

    Fetches messages from Telegram and stores them in the database.
    """
    job_id = UUID(job_data["job_id"])
    channel_id = UUID(job_data["channel_id"])
    username = job_data["username"]
    days = job_data.get("days", 7)

    redis = await _get_redis()

    try:
        # Mark job as running
        await redis.sadd(ACTIVE_JOBS_KEY, json.dumps(job_data))
        await _update_job_status(job_id, "running", stage="initializing")

        logger.info(f"Processing fetch job {job_id} for {username}")

        # Import telegram client dynamically to avoid circular imports
        try:
            from app.services.telegram_client import get_telegram_client
        except ImportError:
            raise RuntimeError(
                "Telegram client not available. Please implement telegram_client.py service."
            )

        telegram_client = get_telegram_client()

        # Update channel info (subscriber count, title, description)
        await _update_job_status(job_id, "running", stage="info")
        try:
            channel_info = await telegram_client.resolve_channel(username)
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select

                result = await db.execute(
                    select(Channel).where(Channel.id == channel_id)
                )
                channel = result.scalar_one_or_none()
                if channel:
                    channel.title = channel_info.get('title') or channel.title
                    channel.description = channel_info.get('description') or channel.description
                    channel.subscriber_count = channel_info.get('subscribers', 0)
                    await db.commit()
                    logger.info(f"Updated channel info for {username}: {channel_info.get('subscribers', 0)} subscribers")
        except (SQLAlchemyError, RuntimeError, KeyError, AttributeError) as e:
            logger.warning(f"Failed to update channel info for {username}: {e}")
            # Continue with fetch even if info update fails

        # Get channel's last known message ID for incremental sync
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select, func

            result = await db.execute(
                select(func.max(Message.telegram_message_id))
                .where(Message.channel_id == channel_id)
            )
            last_msg_id = result.scalar() or 0

        await _update_job_status(job_id, "running", stage="fetching")

        # Fetch messages in batches
        total_fetched = 0
        new_messages = 0
        batch_size = settings.telegram_batch_size

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Fetch messages (newest first)
        messages = await telegram_client.get_messages(
            username,
            limit=batch_size,
            min_id=last_msg_id,
            offset_date=None  # Get latest first
        )

        while messages:
            total_fetched += len(messages)

            # Process and store messages
            async with AsyncSessionLocal() as db:
                for msg in messages:
                    # Skip if too old
                    if msg.date and msg.date.replace(tzinfo=timezone.utc) < cutoff_date:
                        continue

                    # Skip if already exists
                    from sqlalchemy import select
                    existing = await db.execute(
                        select(Message).where(
                            Message.channel_id == channel_id,
                            Message.telegram_message_id == msg.id
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue

                    # Determine media type
                    media_type = None
                    media_urls = []
                    if msg.photo:
                        media_type = "photo"
                    elif msg.video:
                        media_type = "video"
                    elif msg.document:
                        media_type = "document"
                    elif msg.audio:
                        media_type = "audio"

                    # Create message record
                    new_msg = Message(
                        channel_id=channel_id,
                        telegram_message_id=msg.id,
                        original_text=msg.text or msg.message or "",
                        media_type=media_type,
                        media_urls=media_urls,
                        published_at=msg.date.replace(tzinfo=timezone.utc) if msg.date else datetime.now(timezone.utc),
                        fetched_at=datetime.now(timezone.utc),
                        needs_translation=bool(msg.text or msg.message)
                    )
                    db.add(new_msg)
                    new_messages += 1

                await db.commit()

                # Trigger immediate translation for new messages (non-blocking)
                # Extract serialized data while still in session context
                from app.services.translation_service import translate_message_immediate

                if new_messages > 0:
                    # Collect message data for translation BEFORE session closes
                    # Query the messages we just added to get their IDs
                    recent_result = await db.execute(
                        select(Message.id, Message.original_text, Message.channel_id)
                        .where(Message.channel_id == channel_id)
                        .where(Message.needs_translation.is_(True))
                        .order_by(Message.published_at.desc())
                        .limit(new_messages)
                    )
                    messages_to_translate = recent_result.all()

                    # Create async tasks with serialized data
                    for msg_id, text, ch_id in messages_to_translate:
                        if text and text.strip():
                            asyncio.create_task(
                                translate_message_immediate(msg_id, text, ch_id)
                            )

            # Update progress
            await _update_job_status(
                job_id, "running",
                stage="fetching",
                total=total_fetched,
                new=new_messages,
                processed=total_fetched
            )

            # Check if we've gone past the cutoff date
            if messages and messages[-1].date:
                oldest_date = messages[-1].date.replace(tzinfo=timezone.utc)
                if oldest_date < cutoff_date:
                    break

            # Get next batch (older messages)
            if messages:
                messages = await telegram_client.get_messages(
                    username,
                    limit=batch_size,
                    min_id=last_msg_id,
                    offset_date=messages[-1].date
                )
            else:
                break

        # Mark as completed
        await _update_job_status(
            job_id, "completed",
            stage="done",
            total=total_fetched,
            new=new_messages,
            processed=total_fetched
        )

        logger.info(
            f"Fetch job {job_id} completed: {total_fetched} total, {new_messages} new messages"
        )

    except (RedisError, SQLAlchemyError, RuntimeError, ValueError, KeyError, AttributeError) as e:
        logger.exception(f"Fetch job {job_id} failed: {e}")
        await _update_job_status(job_id, "failed", error=str(e))

    finally:
        # Remove from active jobs
        await redis.srem(ACTIVE_JOBS_KEY, json.dumps(job_data))


async def _fetch_worker(worker_id: int) -> None:
    """Background worker that processes fetch jobs from the queue."""
    logger.info(f"Fetch worker {worker_id} started")
    redis = await _get_redis()

    while not _shutdown_event.is_set():
        try:
            # Block-pop from queue with timeout
            result = await redis.blpop(FETCH_QUEUE_KEY, timeout=5)

            if result:
                _, job_json = result
                job_data = json.loads(job_json)
                await _process_fetch_job(job_data)

        except asyncio.CancelledError:
            break
        except (RedisError, SQLAlchemyError, RuntimeError, ValueError, KeyError, AttributeError) as e:
            logger.exception(f"Fetch worker {worker_id} error: {e}")
            await asyncio.sleep(5)  # Back off on error

    logger.info(f"Fetch worker {worker_id} stopped")


async def start_fetch_worker() -> None:
    """Start the fetch worker pool."""
    global _worker_tasks, _shutdown_event

    if _worker_tasks:
        logger.warning("Fetch workers already running")
        return

    _shutdown_event = asyncio.Event()
    num_workers = settings.telegram_fetch_workers

    for i in range(num_workers):
        task = asyncio.create_task(_fetch_worker(i))
        _worker_tasks.append(task)

    logger.info(f"Started {num_workers} fetch workers")


async def stop_fetch_worker() -> None:
    """Stop all fetch workers gracefully."""
    global _worker_tasks, _shutdown_event

    if not _worker_tasks:
        return

    logger.info("Stopping fetch workers...")
    _shutdown_event.set()

    # Wait for workers to finish
    for task in _worker_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    _worker_tasks.clear()
    _shutdown_event = None
    logger.info("Fetch workers stopped")


async def get_queue_length() -> int:
    """Get number of jobs waiting in queue."""
    redis = await _get_redis()
    return await redis.llen(FETCH_QUEUE_KEY)


async def get_active_jobs_count() -> int:
    """Get number of jobs currently being processed."""
    redis = await _get_redis()
    return await redis.scard(ACTIVE_JOBS_KEY)
