"""Message Translation Bulk Service

This module provides functions for translating messages in bulk and on-demand.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.message import Message, MessageTranslation
from app.models.channel import Channel, user_channels
from app.services.translation_pool import run_translation
from app.services.translator import translator

logger = logging.getLogger(__name__)


async def translate_messages_batch(
    user_id: UUID,
    target_language: str,
    channel_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """Translate messages in batch for a user.

    Args:
        user_id: UUID of the user requesting the translation
        target_language: Target language code for translation
        channel_id: Optional channel ID to filter messages

    Returns:
        Dictionary with translation statistics including:
        - message: Summary message
        - duration_seconds: Time taken to process
    """
    async with AsyncSessionLocal() as db_local:
        query = select(Message.id, Message.original_text, Message.published_at).where(
            Message.needs_translation.is_(True)
        )
        query = query.join(Channel, Message.channel_id == Channel.id).join(
            user_channels,
            and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user_id)
        )

        if channel_id:
            query = query.where(Message.channel_id == channel_id)

        result = await db_local.execute(query)
        messages_to_translate = [
            {'id': row.id, 'original_text': row.original_text, 'published_at': row.published_at}
            for row in result.all()
            if row.original_text
        ]

    if not messages_to_translate:
        return {"message": "No messages to translate", "duration_seconds": 0}

    translated_count = 0
    start_time = datetime.now()

    message_ids = [m['id'] for m in messages_to_translate]
    cache_hits = {}

    async with AsyncSessionLocal() as db_local:
        cache_query = select(MessageTranslation).where(
            MessageTranslation.message_id.in_(message_ids),
            MessageTranslation.target_lang == target_language
        )
        cache_result = await db_local.execute(cache_query)
        for row in cache_result.scalars().all():
            cache_hits[row.message_id] = row

    to_batch_process = []
    messages_with_cache = []

    for msg in messages_to_translate:
        if msg['id'] in cache_hits:
            messages_with_cache.append((msg, cache_hits[msg['id']]))
        else:
            to_batch_process.append(msg)

    updates = []
    if messages_with_cache:
        for msg, cached in messages_with_cache:
            updates.append({
                'id': msg['id'],
                'translated_text': cached.translated_text,
                'source_language': 'detected-cache',
                'target_language': target_language,
                'needs_translation': False,
                'translated_at': datetime.now(timezone.utc),
                'translation_priority': 'cached',
            })
            translated_count += 1

    if to_batch_process:
        texts = [m['original_text'] for m in to_batch_process]
        published_dates = [m['published_at'] for m in to_batch_process]

        batch_results = await run_translation(
            translator.translate_batch(
                texts,
                target_lang=target_language,
                published_at_list=published_dates,
            )
        )

        new_translations = []

        for msg, (trans_text, source_lang, priority) in zip(to_batch_process, batch_results):
            updates.append({
                'id': msg['id'],
                'translated_text': trans_text,
                'source_language': source_lang,
                'target_language': target_language,
                'needs_translation': False,
                'translated_at': datetime.now(timezone.utc),
                'translation_priority': priority,
            })

            if trans_text:
                new_translations.append({
                    'message_id': msg['id'],
                    'target_lang': target_language,
                    'translated_text': trans_text,
                    'translated_by': user_id,
                })

            translated_count += 1

        if new_translations:
            async with AsyncSessionLocal() as db_local:
                from sqlalchemy.dialects.postgresql import insert as pg_insert
                stmt = pg_insert(MessageTranslation).values(new_translations)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=['message_id', 'target_lang']
                )
                await db_local.execute(stmt)
                await db_local.commit()

    if updates:
        async with AsyncSessionLocal() as db_local:
            chunk_size = 100
            for i in range(0, len(updates), chunk_size):
                chunk = updates[i:i + chunk_size]
                await db_local.execute(
                    update(Message),
                    chunk
                )
            await db_local.commit()

    duration = datetime.now() - start_time
    return {
        "message": f"Processed {translated_count} messages (Cache hits: {len(messages_with_cache)})",
        "duration_seconds": duration.total_seconds()
    }


async def translate_single_message(
    message_id: UUID,
    target_language: str,
) -> Message:
    """Translate a single message on demand.

    Args:
        message_id: UUID of the message to translate
        target_language: Target language code for translation

    Returns:
        The updated Message object with translation

    Raises:
        ValueError: If message not found or has no text to translate
    """
    async with AsyncSessionLocal() as db_local:
        result = await db_local.execute(
            select(Message).options(selectinload(Message.channel)).where(Message.id == message_id)
        )
        message = result.scalar_one_or_none()

    if not message:
        raise ValueError("Message not found")

    if not message.needs_translation:
        return message

    original_text = message.original_text or ""
    if not original_text.strip():
        async with AsyncSessionLocal() as db_local:
            await db_local.execute(
                update(Message)
                .where(Message.id == message_id)
                .values(needs_translation=False, translation_priority="skip")
            )
            await db_local.commit()
        message.needs_translation = False
        return message

    translated_text, source_lang, priority = await run_translation(
        translator.translate(
            original_text,
            source_lang=message.source_language,
            target_lang=target_language,
            published_at=message.published_at,
        )
    )

    async with AsyncSessionLocal() as db_local:
        await db_local.execute(
            update(Message)
            .where(Message.id == message_id)
            .values(
                translated_text=translated_text,
                source_language=source_lang,
                target_language=target_language,
                needs_translation=False,
                translated_at=datetime.now(timezone.utc),
                translation_priority=priority,
            )
        )
        await db_local.commit()
        refreshed = await db_local.execute(
            select(Message).options(selectinload(Message.channel)).where(Message.id == message_id)
        )
        message = refreshed.scalar_one_or_none()

    if not message:
        raise ValueError("Message not found after translation")

    return message
