import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from telethon.errors import FloodWaitError

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.channel import Channel
from app.models.fetch_job import FetchJob
from app.models.message import Message
from app.services.message_bulk import bulk_insert_messages
from app.services.telegram_collector import fetch_historical_with_lock, get_channel_info_with_lock, iter_historical_with_lock

logger = logging.getLogger(__name__)
settings = get_settings()

# Maximum retries for FloodWaitError before giving up
MAX_FLOOD_RETRIES = 3

# Job queue and parallel worker management
_queue: asyncio.Queue[UUID] = asyncio.Queue()
_active_jobs: set[UUID] = set()
_active_jobs_lock = asyncio.Lock()
_worker_tasks: list[asyncio.Task] = []
_worker_lock = asyncio.Lock()

# Fetch concurrency semaphore (separate from Telegram operations)
_fetch_semaphore: Optional[asyncio.Semaphore] = None


def _get_fetch_semaphore() -> asyncio.Semaphore:
    """Get or create fetch semaphore."""
    global _fetch_semaphore
    if _fetch_semaphore is None:
        _fetch_semaphore = asyncio.Semaphore(settings.fetch_workers)
    return _fetch_semaphore


async def start_fetch_worker() -> None:
    """Start the background workers and hydrate pending jobs.

    Starts multiple parallel workers (configurable via fetch_workers setting)
    to process fetch jobs concurrently.
    """
    global _worker_tasks
    async with _worker_lock:
        # Check if workers are already running
        running_workers = [t for t in _worker_tasks if not t.done()]
        if len(running_workers) >= settings.fetch_workers:
            return

        await _enqueue_pending_jobs()

        # Start workers up to the configured limit
        workers_to_start = settings.fetch_workers - len(running_workers)
        for i in range(workers_to_start):
            worker_id = len(running_workers) + i + 1
            task = asyncio.create_task(_fetch_worker(worker_id))
            _worker_tasks.append(task)

        logger.info(
            "Started %d fetch workers (total: %d)",
            workers_to_start,
            settings.fetch_workers
        )


async def stop_fetch_worker() -> None:
    """Stop all background workers."""
    global _worker_tasks
    async with _worker_lock:
        if not _worker_tasks:
            return

        for task in _worker_tasks:
            task.cancel()

        # Wait for all workers to finish
        await asyncio.gather(*_worker_tasks, return_exceptions=True)
        _worker_tasks = []
        logger.info("All fetch queue workers stopped")


async def enqueue_fetch_job(channel_id: UUID, username: str, days: int) -> FetchJob:
    """Create a fetch job and enqueue it for sequential processing."""
    async with AsyncSessionLocal() as db:
        existing_result = await db.execute(
            select(FetchJob).where(
                FetchJob.channel_id == channel_id,
                FetchJob.status.in_(("queued", "running")),
            )
        )
        existing_job = existing_result.scalar_one_or_none()
        if existing_job:
            return existing_job

        job = FetchJob(
            channel_id=channel_id,
            days=days,
            status="queued",
            stage="queued",
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

    await _queue.put(job.id)
    logger.info("Queued fetch job %s for %s (%sd)", job.id, username, days)
    return job


async def _enqueue_pending_jobs() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(FetchJob.id)
            .where(FetchJob.status == "queued")
            .order_by(FetchJob.created_at.asc())
        )
        for job_id in result.scalars().all():
            if job_id in _active_jobs:
                continue
            _queue.put_nowait(job_id)


async def _fetch_worker(worker_id: int) -> None:
    """Parallel fetch worker that processes jobs from the queue.

    Args:
        worker_id: Unique identifier for this worker (for logging)
    """
    logger.info("Fetch worker %d started", worker_id)
    while True:
        job_id = await _queue.get()
        should_process = False
        try:
            # Use lock to safely check/modify active jobs set atomically
            # The job stays in _active_jobs for the entire processing duration
            async with _active_jobs_lock:
                if job_id in _active_jobs:
                    # Job is already being processed by another worker
                    _queue.task_done()
                    continue
                # Mark as active before releasing lock to prevent double-start
                _active_jobs.add(job_id)
                should_process = True

            # Now process the job (lock released, but job_id is in _active_jobs)
            logger.info("Worker %d processing job %s", worker_id, job_id)
            async with _get_fetch_semaphore():
                await _run_job(job_id)
            logger.info("Worker %d completed job %s", worker_id, job_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Worker %d: unhandled error in job %s", worker_id, job_id)
        finally:
            # Only remove from active set if we added it
            if should_process:
                async with _active_jobs_lock:
                    _active_jobs.discard(job_id)
            _queue.task_done()


async def _fetch_with_flood_retry(func, job_id: UUID, *args, **kwargs):
    """Execute a Telegram API function with FloodWaitError retry handling.

    Args:
        func: The async function to call (e.g., get_channel_info_with_lock)
        job_id: The job ID for logging and error marking
        *args, **kwargs: Arguments to pass to the function

    Returns:
        The result of the function call, or None if max retries exceeded
    """
    retries = 0
    while retries < MAX_FLOOD_RETRIES:
        try:
            return await func(*args, **kwargs)
        except FloodWaitError as e:
            retries += 1
            wait_time = e.seconds
            logger.warning(
                "FloodWaitError for job %s: waiting %ds (retry %d/%d)",
                job_id, wait_time, retries, MAX_FLOOD_RETRIES
            )
            if retries >= MAX_FLOOD_RETRIES:
                await _mark_failed(
                    job_id,
                    f"FloodWaitError: max retries ({MAX_FLOOD_RETRIES}) exceeded. "
                    f"Last wait required: {wait_time}s"
                )
                return None
            await asyncio.sleep(wait_time)
    return None


async def _run_job(job_id: UUID) -> None:
    async with AsyncSessionLocal() as db:
        job = await db.get(FetchJob, job_id)
        if not job:
            return
        if job.status not in ("queued", "running"):
            return
        channel = await db.get(Channel, job.channel_id)
        if not channel:
            job.status = "failed"
            job.stage = "failed"
            job.error_message = "Channel not found"
            job.finished_at = datetime.now(timezone.utc)
            await db.commit()
            return

        job.status = "running"
        job.stage = "info"
        job.started_at = datetime.now(timezone.utc)
        job.error_message = None
        await db.commit()

        username = channel.username
        channel_id = channel.id
        days = None if job.days == 0 else job.days

    # Phase 1: Update Channel Info
    try:
        await _update_job(job_id, stage="info")
        channel_info = await _fetch_with_flood_retry(
            get_channel_info_with_lock, job_id, username
        )
        if channel_info is None:
            return
        await _update_channel_info(channel_id, channel_info)
    except Exception as exc:
        await _mark_failed(job_id, str(exc))
        return

    # Phase 2: Streaming Fetch
    await _update_job(job_id, stage="fetching")
    
    last_message_id = 0
    total_new = 0
    
    # Retry loop for resuming after FloodWait
    while True:
        try:
            # iter_historical_with_lock yields batches. We must consume them.
            # If FloodWaitError occurs during iteration, it bubbles up here.
            async for batch in iter_historical_with_lock(username, offset_id=last_message_id, days=days):
                if not batch:
                    continue
                
                # Identify new messages
                msg_ids = [m['message_id'] for m in batch]
                async with AsyncSessionLocal() as db:
                    existing_result = await db.execute(
                        select(Message.telegram_message_id).where(
                            Message.channel_id == channel_id,
                            Message.telegram_message_id.in_(msg_ids)
                        )
                    )
                    existing_ids = set(existing_result.scalars().all())

                new_messages_data = [m for m in batch if m['message_id'] not in existing_ids]
                
                if new_messages_data:
                    pending = [
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
                            'fetched_at': datetime.now(timezone.utc),
                        }
                        for msg_data in new_messages_data
                    ]
                    
                    async with AsyncSessionLocal() as db:
                        await bulk_insert_messages(db, pending)
                        await db.commit()
                    
                    total_new += len(new_messages_data)
                    
                    # Update job progress using direct DB call to avoid stale object issues
                    async with AsyncSessionLocal() as db:
                        job = await db.get(FetchJob, job_id)
                        if job:
                            job.new_messages = (job.new_messages or 0) + len(new_messages_data)
                            job.processed_messages = (job.processed_messages or 0) + len(batch)
                            job.stage = "saving" # Indicates we are actively saving data
                            await db.commit()

                # Update checkpoint (telethon iter_messages goes Newest -> Oldest)
                # So we want the SMALLEST ID in this batch to be the offset for the next
                min_id_in_batch = min(m['message_id'] for m in batch)
                last_message_id = min_id_in_batch

        except FloodWaitError as e:
            wait_time = e.seconds + 2 # Add small buffer
            logger.warning(f"FloodWaitError in streaming fetch job {job_id}: waiting {wait_time}s before resuming from {last_message_id}")
            await asyncio.sleep(wait_time)
            continue # Resume loop with last_message_id
            
        except Exception as exc:
            logger.exception(f"Error in streaming fetch job {job_id}")
            await _mark_failed(job_id, str(exc))
            return
            
        # If we exit the loop normally (async for finishes), break outer loop
        break

    await _update_channel_last_fetched(channel_id)
    await _mark_completed(job_id)


async def _update_job(job_id: UUID, **fields) -> None:
    if not fields:
        return
    async with AsyncSessionLocal() as db:
        job = await db.get(FetchJob, job_id)
        if not job:
            return
        for key, value in fields.items():
            setattr(job, key, value)
        await db.commit()


async def _mark_failed(job_id: UUID, error_message: str) -> None:
    await _update_job(
        job_id,
        status="failed",
        stage="failed",
        error_message=error_message,
        finished_at=datetime.now(timezone.utc),
    )


async def _mark_completed(job_id: UUID, new_messages: Optional[int] = None) -> None:
    fields = {
        "status": "completed",
        "stage": "completed",
        "finished_at": datetime.now(timezone.utc),
    }
    if new_messages is not None:
        fields["new_messages"] = new_messages
    await _update_job(job_id, **fields)


async def _update_channel_last_fetched(channel_id: UUID) -> None:
    async with AsyncSessionLocal() as db:
        channel = await db.get(Channel, channel_id)
        if channel:
            channel.last_fetched_at = datetime.now(timezone.utc)
            await db.commit()


async def _update_channel_info(channel_id: UUID, channel_info: dict) -> None:
    async with AsyncSessionLocal() as db:
        channel = await db.get(Channel, channel_id)
        if not channel:
            return
        channel.telegram_id = channel_info.get("id")
        channel.title = channel_info.get("title") or channel.username
        channel.description = channel_info.get("description") or ""
        channel.subscriber_count = channel_info.get("participants_count") or 0
        await db.commit()
