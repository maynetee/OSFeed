"""Translation Service - Immediate Message Translation

This module provides immediate (fire-and-forget) translation for messages.
Called after message ingestion to translate content in the background.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.message import Message
from app.config import get_settings
from app.services.translator import translator
from app.services.translation_pool import run_translation
from app.services.events import publish_message_translated

logger = logging.getLogger(__name__)
settings = get_settings()


async def translate_message_immediate(
    message_id: UUID,
    original_text: str,
    channel_id: UUID,
    target_language: str = None,
    source_language: str = None
) -> bool:
    """Translate a message immediately after ingestion.

    This function:
    1. Opens its own DB session (receives serialized data, not ORM objects)
    2. Checks if translation is needed
    3. Uses translation pool for rate limiting
    4. Updates message in database
    5. Publishes event on success

    Args:
        message_id: UUID of the message to translate
        original_text: Original message text
        channel_id: UUID of the channel containing the message
        target_language: Target language code (defaults to settings.preferred_language)
        source_language: Optional source language code (will auto-detect if not provided)

    Returns:
        True if translation succeeded, False otherwise
    """
    try:
        # 1. Check if text is empty/whitespace
        if not original_text or not original_text.strip():
            logger.debug(f"Message {message_id}: empty text, skipping translation")
            return False

        # 2. Open DB session
        async with AsyncSessionLocal() as db:
            # 3. Fetch message to check needs_translation
            stmt = select(Message).where(Message.id == message_id)
            result = await db.execute(stmt)
            message = result.scalar_one_or_none()

            if not message:
                logger.warning(f"Message {message_id} not found in database")
                return False

            if not message.needs_translation:
                logger.debug(f"Message {message_id}: already translated, skipping")
                return False

            # 4. Determine target language
            if not target_language:
                target_language = message.target_language or settings.preferred_language

            # 5. Call translator through translation pool
            translated_text, detected_lang, priority = await run_translation(
                translator.translate(
                    original_text,
                    source_lang=source_language,
                    target_lang=target_language,
                    published_at=message.published_at
                )
            )

            # If priority is "skip", the translator decided not to translate
            if priority == "skip":
                logger.debug(f"Message {message_id}: translation skipped (priority={priority})")
                return False

            # 6. Update message in DB
            message.translated_text = translated_text
            message.source_language = detected_lang
            message.target_language = target_language
            message.needs_translation = False
            message.translated_at = datetime.now(timezone.utc)
            message.translation_priority = priority

            # 7. Commit changes
            await db.commit()

            logger.info(
                f"Message {message_id}: translated from {detected_lang} to {target_language} "
                f"(priority={priority})"
            )

            # 8. Publish event
            await publish_message_translated(
                message_id=message_id,
                channel_id=channel_id,
                translated_text=translated_text,
                source_language=detected_lang,
                target_language=target_language
            )

            return True

    except Exception as e:
        logger.exception(f"Failed to translate message {message_id}: {e}")
        return False
