from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, timezone
from app.models.channel import Channel
from app.models.message import Message
from app.services.telegram_collector import TelegramCollector
from app.services.translator import translator
from app.services.deduplicator import deduplicator
from app.database import AsyncSessionLocal
from app.config import get_settings
import json


settings = get_settings()


async def collect_messages_job():
    """
    Background job to collect messages from all followed channels.

    IMPORTANT: This job releases the database lock during slow I/O operations
    (Telegram API calls, translation) to prevent blocking other database operations.
    """
    print(f"[{datetime.utcnow()}] Starting message collection job...")

    # Step 1: Get all channels (short DB session)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Channel))
        channels = result.scalars().all()
        # Extract channel data before closing session
        channel_data = [(c.id, c.username) for c in channels]

    if not channel_data:
        print("No channels to collect from")
        return

    collector = TelegramCollector()
    total_new_messages = 0

    for channel_id, channel_username in channel_data:
        print(f"Collecting messages from {channel_username}...")

        try:
            # Step 2: Fetch messages from Telegram (NO DB session held)
            messages = await collector.get_recent_messages(channel_username, limit=20)

            if not messages:
                continue

            # Step 3: Get existing message IDs (short DB session)
            async with AsyncSessionLocal() as db:
                existing_result = await db.execute(
                    select(Message.telegram_message_id).where(
                        Message.channel_id == channel_id,
                        Message.telegram_message_id.in_([m['message_id'] for m in messages])
                    )
                )
                existing_ids = set(existing_result.scalars().all())

            # Filter to only new messages
            new_msg_data = [m for m in messages if m['message_id'] not in existing_ids]

            if not new_msg_data:
                # Update last_fetched_at even if no new messages
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(Channel).where(Channel.id == channel_id))
                    channel = result.scalar_one_or_none()
                    if channel:
                        channel.last_fetched_at = datetime.utcnow()
                        await db.commit()
                continue

            # Step 4: Translate messages (NO DB session held - this is slow)
            translated_messages = []
            for msg_data in new_msg_data:
                translated_text, source_lang = await translator.translate(msg_data['text'])
                translated_messages.append({
                    'telegram_message_id': msg_data['message_id'],
                    'original_text': msg_data['text'],
                    'translated_text': translated_text,
                    'source_language': source_lang,
                    'target_language': settings.preferred_language,
                    'media_type': msg_data.get('media_type'),
                    'media_urls': json.dumps(msg_data.get('media_urls', [])),
                    'published_at': msg_data['date'],
                    'translated_at': datetime.now(timezone.utc),
                })

            # Step 5: Save translated messages to DB (short DB session)
            async with AsyncSessionLocal() as db:
                for msg in translated_messages:
                    message = Message(
                        channel_id=channel_id,
                        telegram_message_id=msg['telegram_message_id'],
                        original_text=msg['original_text'],
                        translated_text=msg['translated_text'],
                        source_language=msg['source_language'],
                        target_language=msg['target_language'],
                        media_type=msg['media_type'],
                        media_urls=msg['media_urls'],
                        published_at=msg['published_at'],
                        translated_at=msg['translated_at'],
                    )
                    db.add(message)

                # Also update channel's last_fetched_at
                result = await db.execute(select(Channel).where(Channel.id == channel_id))
                channel = result.scalar_one_or_none()
                if channel:
                    channel.last_fetched_at = datetime.utcnow()

                await db.commit()
                print(f"Added {len(translated_messages)} new messages from {channel_username}")
                total_new_messages += len(translated_messages)

        except Exception as e:
            print(f"Error collecting from {channel_username}: {e}")
            continue

    await collector.disconnect()

    # Step 6: Run cross-channel deduplication (separate short DB sessions)
    if total_new_messages > 0:
        print("Running cross-channel deduplication...")
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

        async with AsyncSessionLocal() as db:
            all_recent = await db.execute(
                select(Message)
                .where(Message.published_at >= cutoff_time)
                .order_by(Message.published_at.desc())
            )
            recent_messages = list(all_recent.scalars().all())

            if recent_messages:
                deduplicator.mark_duplicates(recent_messages, cutoff_time=cutoff_time)
                await db.commit()
                print(f"Deduplication completed for {len(recent_messages)} messages")

    print(f"[{datetime.utcnow()}] Message collection job completed")
