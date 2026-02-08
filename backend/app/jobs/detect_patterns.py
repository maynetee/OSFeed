"""Background job to detect intelligence patterns. Runs every 15 minutes."""

import logging

from app.jobs.retry import retry

logger = logging.getLogger(__name__)


@retry(max_attempts=3)
async def detect_patterns_job():
    """Run pattern detection algorithms."""
    from app.services.pattern_service import pattern_service
    await pattern_service.run_detection()
