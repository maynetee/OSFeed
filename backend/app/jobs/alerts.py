import logging
from datetime import datetime, timedelta, timezone

from redis.exceptions import RedisError
from sqlalchemy import func, or_, select

from app.database import AsyncSessionLocal
from app.models.alert import Alert, AlertTrigger
from app.models.channel import Channel
from app.models.collection import Collection, collection_channels
from app.models.message import Message
from app.models.notification import Notification
from app.models.user import User
from app.services.email_service import email_service
from app.services.events import publish_alert_triggered

logger = logging.getLogger(__name__)


def _escape_like(s: str) -> str:
    """Escape ILIKE special characters."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _should_run(alert: Alert) -> bool:
    if not alert.last_triggered_at:
        return True
    now = datetime.now(timezone.utc)
    if alert.frequency == "hourly":
        return alert.last_triggered_at <= now - timedelta(hours=1)
    if alert.frequency == "daily":
        return alert.last_triggered_at <= now - timedelta(days=1)
    return alert.last_triggered_at <= now - timedelta(minutes=2)


async def evaluate_alerts_job():
    now = datetime.now(timezone.utc)
    logger.info(f"[{now}] Starting alert evaluation job...")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Alert).where(Alert.is_active == True))
        alerts = result.scalars().all()

        for alert in alerts:
            if not _should_run(alert):
                alert.last_evaluated_at = now
                continue

            collection_result = await session.execute(
                select(Collection).where(Collection.id == alert.collection_id)
            )
            collection = collection_result.scalar_one_or_none()
            if not collection:
                alert.last_evaluated_at = now
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
                alert.last_evaluated_at = now
                continue

            window_minutes = 2 if alert.frequency == "realtime" else 60 if alert.frequency == "hourly" else 24 * 60
            window_start = now - timedelta(minutes=window_minutes)

            query = (
                select(Message)
                .where(Message.channel_id.in_(channel_ids))
                .where(Message.published_at >= window_start)
            )

            # Build keyword filters based on match_mode
            keywords = alert.keywords or []
            if keywords:
                if alert.match_mode == "all":
                    for keyword in keywords:
                        like_pattern = f"%{_escape_like(keyword)}%"
                        query = query.where(
                            or_(
                                Message.translated_text.ilike(like_pattern),
                                Message.original_text.ilike(like_pattern),
                            )
                        )
                else:
                    keyword_filters = []
                    for keyword in keywords:
                        like_pattern = f"%{_escape_like(keyword)}%"
                        keyword_filters.append(Message.translated_text.ilike(like_pattern))
                        keyword_filters.append(Message.original_text.ilike(like_pattern))
                    query = query.where(or_(*keyword_filters))

            if alert.entities:
                entity_filters = []
                for entity in alert.entities:
                    entity_filters.append(Message.entities.contains({"persons": [entity]}))
                    entity_filters.append(Message.entities.contains({"locations": [entity]}))
                    entity_filters.append(Message.entities.contains({"organizations": [entity]}))
                query = query.where(or_(*entity_filters))

            # Dedup: get message IDs already triggered for this alert
            existing_triggers = await session.execute(
                select(AlertTrigger.message_ids).where(AlertTrigger.alert_id == alert.id)
            )
            already_triggered_ids = set()
            for row in existing_triggers.scalars().all():
                if row:
                    already_triggered_ids.update(row)

            messages_result = await session.execute(query.order_by(Message.published_at.desc()).limit(50))
            matched_messages = messages_result.scalars().all()

            # Filter out already-triggered messages
            new_messages = [m for m in matched_messages if str(m.id) not in already_triggered_ids]

            if len(new_messages) < (alert.min_threshold or 1):
                alert.last_evaluated_at = now
                continue

            message_ids = [str(m.id) for m in new_messages[:20]]

            summary = f"{len(new_messages)} matching messages in the last {window_minutes} minutes."
            trigger = AlertTrigger(
                alert_id=alert.id,
                message_ids=message_ids,
                summary=summary,
            )
            session.add(trigger)
            alert.last_triggered_at = now
            alert.last_evaluated_at = now

            # Check rate limit: count notifications for this user in the last hour
            rate_limit_window = now - timedelta(hours=1)
            rate_count_result = await session.execute(
                select(func.count()).where(
                    Notification.user_id == alert.user_id,
                    Notification.type == "alert_triggered",
                    Notification.created_at >= rate_limit_window,
                )
            )
            notifications_in_hour = rate_count_result.scalar() or 0

            # If rate limit exceeded, skip notification and email but still commit the trigger
            if notifications_in_hour >= 10:
                logger.warning(
                    f"Rate limit reached for user {alert.user_id}: {notifications_in_hour} "
                    f"notifications in last hour, skipping notification for alert {alert.name}"
                )
            else:
                # Create in-app notification
                notification = Notification(
                    user_id=alert.user_id,
                    type="alert_triggered",
                    title=f"Alert: {alert.name}",
                    body=summary,
                    link=f"/alerts/{alert.id}",
                    metadata_={
                        "alert_id": str(alert.id),
                        "matched_keywords": keywords,
                        "message_count": len(new_messages),
                    },
                )
                session.add(notification)

                # Flush to get trigger.id before publishing event
                await session.flush()

                # Publish alert:triggered event with user_id for frontend targeting
                try:
                    await publish_alert_triggered(
                        alert_id=alert.id,
                        trigger_id=trigger.id,
                        alert_name=alert.name,
                        summary=summary,
                        message_count=len(new_messages),
                        user_id=alert.user_id,
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
                            # Prepare message preview from first matched message
                            message_preview = ""
                            if new_messages:
                                first_msg = new_messages[0]
                                preview_text = first_msg.translated_text or first_msg.original_text or ""
                                message_preview = preview_text[:200] if preview_text else ""

                            success = await email_service.send_alert_triggered(
                                email=user.email,
                                alert_name=alert.name,
                                summary=summary,
                                message_count=len(new_messages),
                                keywords=keywords,
                                message_preview=message_preview,
                                alert_id=str(alert.id),
                            )
                            if success:
                                logger.debug(f"Sent email notification for alert {alert.name} to {user.email}")
                            else:
                                logger.warning(f"Failed to send email notification for alert {alert.name}")
                    except Exception as e:
                        logger.error(f"Failed to send email notification for alert {alert.name}: {e}")

        await session.commit()

    logger.info(f"[{datetime.now(timezone.utc)}] Alert evaluation job completed")
