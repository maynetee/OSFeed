import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.digest_preference import DigestPreference
from app.models.user import User
from app.services.digest_service import build_digest_content, send_digest_email

logger = logging.getLogger(__name__)


async def send_daily_digests_job():
    """Hourly job: send digests to users whose send_hour matches current UTC hour."""
    now = datetime.now(timezone.utc)
    current_hour = now.hour
    logger.info(f"[{now}] Starting digest job for hour {current_hour} UTC...")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DigestPreference)
            .where(DigestPreference.enabled.is_(True))
            .where(DigestPreference.send_hour == current_hour)
        )
        preferences = result.scalars().all()

        if not preferences:
            logger.info(f"No digest preferences for hour {current_hour} UTC")
            return

        sent_count = 0
        for pref in preferences:
            try:
                user_result = await session.execute(
                    select(User).where(User.id == pref.user_id)
                )
                user = user_result.scalar_one_or_none()
                if not user or not user.email:
                    continue

                # Check frequency: for weekly, only send on Mondays
                if pref.frequency == "weekly" and now.weekday() != 0:
                    continue

                content = await build_digest_content(
                    user=user,
                    collection_ids=pref.collection_ids,
                    max_messages=pref.max_messages or 20,
                    session=session,
                )

                if not content["collections"]:
                    logger.debug(f"No content for digest of user {user.id}, skipping")
                    continue

                success = await send_digest_email(user=user, content=content)
                if success:
                    pref.last_sent_at = now
                    sent_count += 1
                    logger.info(f"Sent digest to user {user.id}")
                else:
                    logger.warning(f"Failed to send digest to user {user.id}")

            except Exception as e:
                logger.error(f"Error sending digest for user {pref.user_id}: {e}", exc_info=True)

        await session.commit()

    logger.info(f"[{datetime.now(timezone.utc)}] Digest job completed. Sent {sent_count} digests.")
