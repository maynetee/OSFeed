"""Background job to score new messages for escalation. Runs every 5 min."""

import logging

logger = logging.getLogger(__name__)


async def score_escalation_job():
    """Score unscored messages for escalation level."""
    try:
        from app.services.escalation_service import escalation_service
        await escalation_service.batch_score_new_messages()
    except Exception as e:
        logger.error(f"Escalation scoring job failed: {e}")
