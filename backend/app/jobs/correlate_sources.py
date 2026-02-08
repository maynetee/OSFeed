"""Background job to analyze multi-source stories."""

import logging

from app.jobs.retry import retry

logger = logging.getLogger(__name__)


@retry(max_attempts=3)
async def correlate_sources_job():
    """Analyze duplicate groups with 3+ sources for cross-source correlation. Runs every 10 min."""
    try:
        from app.services.correlation_service import correlation_service
        await correlation_service.process_new_correlations()
    except Exception:
        logger.exception("correlate_sources_job failed")
