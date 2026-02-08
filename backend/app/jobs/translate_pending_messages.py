import asyncio
import logging
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select, update

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.jobs.retry import retry
from app.models.message import Message
from app.services.events import publish_message_translated
from app.services.translation_pool import run_translation
from app.services.translation_service import should_channel_translate
from app.services.translator import translator

settings = get_settings()

DEFAULT_BATCH_SIZE = 200

logger = logging.getLogger(__name__)


@retry(max_attempts=3)
async def translate_pending_messages_job(batch_size: int = DEFAULT_BATCH_SIZE) -> None:
    """Translate pending messages in the background."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(
                Message.id,
                Message.original_text,
                Message.target_language,
                Message.source_language,
                Message.published_at,
                Message.channel_id,
            )
            .where(Message.needs_translation.is_(True))
            .where(
                (Message.is_duplicate.is_(False)) | (Message.is_duplicate.is_(None))
            )
            .order_by(Message.published_at.desc())
            .limit(batch_size)
        )
        rows: Sequence[tuple] = result.all()
        logger.info(f"DEBUG: Found {len(rows)} pending messages for translation")

    if not rows:
        return

    empty_ids = [
        row.id for row in rows if not row.original_text or not row.original_text.strip()
    ]
    empty_id_set = set(empty_ids)
    non_empty_rows = [
        row for row in rows if row.id not in empty_id_set
    ]

    # Check which channels need translation based on user language preferences
    channel_ids = set(row.channel_id for row in non_empty_rows)
    channel_translate_status: dict = {}
    for channel_id in channel_ids:
        channel_translate_status[channel_id] = await should_channel_translate(channel_id)

    # Filter rows: skip messages from channels that don't need translation
    skip_translation_ids = [
        row.id for row in non_empty_rows
        if not channel_translate_status.get(row.channel_id, True)
    ]
    skip_translation_id_set = set(skip_translation_ids)
    rows_to_translate = [
        row for row in non_empty_rows if row.id not in skip_translation_id_set
    ]

    if skip_translation_ids:
        logger.info(
            f"Skipping translation for {len(skip_translation_ids)} messages "
            f"(channel language matches all user preferences)"
        )

    translations: list[tuple] = []
    if rows_to_translate:
        grouped: dict[tuple[str, str | None], list] = {}
        for row in rows_to_translate:
            target_lang = row.target_language or settings.preferred_language
            source_lang = row.source_language
            grouped.setdefault((target_lang, source_lang), []).append(row)

        async def _translate_group(
            target_lang: str, source_lang: str | None, items: list
        ) -> list[tuple]:
            texts = [row.original_text for row in items]
            published_at_list = [row.published_at for row in items]
            results = await run_translation(
                translator.translate_batch(
                    texts,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    published_at_list=published_at_list,
                )
            )
            return [
                (row.id, translated_text, detected_lang, target_lang, priority, row.channel_id)
                for row, (translated_text, detected_lang, priority) in zip(items, results)
            ]

        tasks = [
            asyncio.create_task(_translate_group(target_lang, source_lang, items))
            for (target_lang, source_lang), items in grouped.items()
        ]
        for task in asyncio.as_completed(tasks):
            translations.extend(await task)

    async with AsyncSessionLocal() as db:
        if empty_ids:
            await db.execute(
                update(Message)
                .where(Message.id.in_(empty_ids))
                .values(
                    needs_translation=False,
                    translated_at=None,
                    translation_priority="skip",
                )
            )

        # Mark messages from channels that don't need translation as skipped
        if skip_translation_ids:
            await db.execute(
                update(Message)
                .where(Message.id.in_(skip_translation_ids))
                .values(
                    needs_translation=False,
                    translated_at=None,
                    translation_priority="skip",
                )
            )

        # Commit skip updates if there are no translations to process
        if (empty_ids or skip_translation_ids) and not translations:
            await db.commit()

        if translations:
            translated_at = datetime.now(timezone.utc)

            # Collect translation data for events
            translation_events = []

            for message_id, translated_text, source_lang, target_lang, priority, channel_id in translations:
                await db.execute(
                    update(Message)
                    .where(Message.id == message_id)
                    .values(
                        translated_text=translated_text,
                        source_language=source_lang,
                        target_language=target_lang,
                        needs_translation=False,
                        translated_at=translated_at,
                        translation_priority=priority,
                    )
                )

                # Collect for later publishing (after commit)
                translation_events.append({
                    'message_id': message_id,
                    'channel_id': channel_id,
                    'translated_text': translated_text,
                    'source_language': source_lang,
                    'target_language': target_lang,
                })

            await db.commit()

            # Publish events AFTER successful commit
            for event_data in translation_events:
                await publish_message_translated(
                    message_id=event_data['message_id'],
                    channel_id=event_data['channel_id'],
                    translated_text=event_data['translated_text'],
                    source_language=event_data['source_language'],
                    target_language=event_data['target_language']
                )

