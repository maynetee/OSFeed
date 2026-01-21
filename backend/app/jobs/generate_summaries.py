import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User
from app.services.summarizer import generate_daily_summary


logger = logging.getLogger(__name__)


async def generate_summaries_job():
    """
    Background job to generate daily summaries.

    Note: generate_daily_summary now manages its own DB sessions internally
    to avoid holding locks during the slow LLM API call.
    """
    now = datetime.now(timezone.utc)
    logger.info(f"[{now.isoformat()}] Starting summary generation job...")

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.is_active == True))
            users = result.scalars().all()

        if not users:
            summary = await generate_daily_summary()
            logger.info(f"Generated daily summary (ID: {summary.id}) with {summary.message_count} messages")
        else:
            for user in users:
                summary = await generate_daily_summary(user_id=user.id)
                logger.info(f"Generated daily summary for {user.email} (ID: {summary.id})")

    except Exception as e:
        logger.error(f"Error generating summary: {e}", exc_info=True)

    end_time = datetime.now(timezone.utc)
    logger.info(f"[{end_time.isoformat()}] Summary generation job completed")
