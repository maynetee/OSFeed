import asyncio
import functools
import logging
import time
import traceback

from app.metrics import JOB_DURATION, JOB_FAILURE, JOB_SUCCESS

logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """Decorator for async job functions with exponential backoff retry and DLQ."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            start_time = time.monotonic()
            for attempt in range(1, max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)
                    duration = time.monotonic() - start_time
                    JOB_DURATION.labels(job_name=func.__name__).observe(duration)
                    JOB_SUCCESS.labels(job_name=func.__name__).inc()
                    return result
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                        logger.warning(
                            "Job %s failed (attempt %d/%d): %s. Retrying in %.1fs",
                            func.__name__, attempt, max_attempts, e, delay,
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "Job %s failed after %d attempts: %s",
                            func.__name__, max_attempts, e,
                        )
            # All attempts exhausted — record failure metrics
            duration = time.monotonic() - start_time
            JOB_DURATION.labels(job_name=func.__name__).observe(duration)
            JOB_FAILURE.labels(job_name=func.__name__).inc()
            # Write to DLQ
            await _send_to_dlq(
                job_name=func.__name__,
                error=str(last_exception),
                stack_trace=traceback.format_exc(),
                attempts=max_attempts,
            )
            # Also report to Sentry if available
            try:
                import sentry_sdk
                sentry_sdk.capture_exception(last_exception)
            except ImportError:
                pass
        return wrapper
    return decorator


async def _send_to_dlq(job_name: str, error: str, stack_trace: str, attempts: int):
    """Insert a failed job record into the dead letter queue table."""
    from app.database import AsyncSessionLocal
    from app.models.dead_letter import DeadLetterEntry

    try:
        async with AsyncSessionLocal() as session:
            entry = DeadLetterEntry(
                job_name=job_name,
                error=error,
                stack_trace=stack_trace,
                attempts=attempts,
            )
            session.add(entry)
            await session.commit()
            logger.info("Job %s sent to dead letter queue", job_name)
    except Exception as e:
        logger.error("Failed to write to DLQ: %s", e)
