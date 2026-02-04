import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func, or_
from redis.exceptions import RedisError
from app.database import AsyncSessionLocal
from app.models.alert import Alert, AlertTrigger
from app.models.collection import Collection
from app.models.channel import Channel
from app.models.message import Message
from app.models.user import User
from app.models.collection import collection_channels
from app.services.events import publish_alert_triggered
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

def _should_run(alert: Alert) -> bool:
    if not alert.last_triggered_at:
        return True
    now = datetime.utcnow()
    if alert.frequency == "hourly":
        return alert.last_triggered_at <= now - timedelta(hours=1)
    if alert.frequency == "daily":
        return alert.last_triggered_at <= now - timedelta(days=1)
    return alert.last_triggered_at <= now - timedelta(minutes=15)


async def evaluate_alerts_job():
    logger.info(f"[{datetime.utcnow()}] Starting alert evaluation job...")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Alert).where(Alert.is_active == True))
        alerts = result.scalars().all()

        for alert in alerts:
            if not _should_run(alert):
                continue

            collection_result = await session.execute(
                select(Collection).where(Collection.id == alert.collection_id)
            )
            collection = collection_result.scalar_one_or_none()
            if not collection:
                continue

            if collection.is_global:
                channel_result = await session.execute(select(Channel.id).where(Channel.is_active == True))
                channel_ids = [row.id for row in channel_result.all()]
            else:
                channel_result = await session.execute(
                    select(collection_channels.c.channel_id)
                    .where(collection_channels.c.collection_id == collection.id)
                )
                channel_ids = [row.channel_id for row in channel_result.all()]

            if not channel_ids:
                continue

            window_minutes = 15 if alert.frequency == "realtime" else 60 if alert.frequency == "hourly" else 24 * 60
            window_start = datetime.utcnow() - timedelta(minutes=window_minutes)

            query = select(Message).where(Message.channel_id.in_(channel_ids)).where(Message.published_at >= window_start)

            keyword_filters = []
            for keyword in alert.keywords or []:
                like_pattern = f"%{keyword}%"
                keyword_filters.append(Message.translated_text.ilike(like_pattern))
                keyword_filters.append(Message.original_text.ilike(like_pattern))
            if keyword_filters:
                query = query.where(or_(*keyword_filters))

            if alert.entities:
                entity_filters = []
                for entity in alert.entities:
                    entity_filters.append(Message.entities.contains({"persons": [entity]}))
                    entity_filters.append(Message.entities.contains({"locations": [entity]}))
                    entity_filters.append(Message.entities.contains({"organizations": [entity]}))
                query = query.where(or_(*entity_filters))

            count_result = await session.execute(select(func.count()).select_from(query.subquery()))
            count = count_result.scalar() or 0

            if count < (alert.min_threshold or 1):
                continue

            messages_result = await session.execute(query.order_by(Message.published_at.desc()).limit(20))
            messages = messages_result.scalars().all()
            message_ids = [str(message.id) for message in messages]

            summary = f"{count} matching messages in the last {window_minutes} minutes."
            trigger = AlertTrigger(
                alert_id=alert.id,
                message_ids=message_ids,
                summary=summary,
            )
            session.add(trigger)
            alert.last_triggered_at = datetime.utcnow()

            # Flush to get trigger.id before publishing event
            await session.flush()

            # Publish alert:triggered event (fire-and-forget)
            try:
                await publish_alert_triggered(
                    alert_id=alert.id,
                    trigger_id=trigger.id,
                    alert_name=alert.name,
                    summary=summary,
                    message_count=count
                )
                logger.debug(f"Published alert:triggered event for alert {alert.name}")
            except RedisError as e:
                logger.error(f"Failed to publish alert:triggered event for alert {alert.name}: {e}")

            # Send email notification if email channel is enabled
            if alert.notification_channels and 'email' in alert.notification_channels:
                try:
                    user_result = await session.execute(
                        select(User).where(User.id == alert.user_id)
                    )
                    user = user_result.scalar_one_or_none()
                    if user and user.email:
                        success = await email_service.send_alert_triggered(
                            email=user.email,
                            alert_name=alert.name,
                            summary=summary,
                            message_count=count
                        )
                        if success:
                            logger.debug(f"Sent email notification for alert {alert.name} to {user.email}")
                        else:
                            logger.warning(f"Failed to send email notification for alert {alert.name}")
                    else:
                        logger.warning(f"User not found or no email address for alert {alert.name} (user_id: {alert.user_id})")
                except Exception as e:
                    logger.error(f"Failed to send email notification for alert {alert.name}: {e}")

        await session.commit()

    logger.info(f"[{datetime.utcnow()}] Alert evaluation job completed")
