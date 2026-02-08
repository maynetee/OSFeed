import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.jobs.retry import retry
from app.models.message import Message
from app.services.relevance_scoring import RelevanceScoringService

logger = logging.getLogger(__name__)


@retry(max_attempts=3)
async def score_relevance_job():
    """Score unscored messages from the last 48 hours."""
    logger.info(f"[{datetime.now(timezone.utc)}] Starting relevance scoring job...")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    scored = 0

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Message)
            .options(selectinload(Message.channel))
            .where(Message.relevance_score.is_(None))
            .where(Message.published_at >= cutoff)
            .limit(500)
        )
        messages = result.scalars().all()

        for message in messages:
            if not message.channel:
                continue
            score = RelevanceScoringService.compute_score(message, message.channel)
            message.relevance_score = score
            scored += 1

        await session.commit()

    logger.info(f"[{datetime.now(timezone.utc)}] Relevance scoring job completed: {scored} messages scored")
