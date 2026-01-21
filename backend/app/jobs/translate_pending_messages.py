from datetime import datetime
import logging
import asyncio
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select, update

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.message import Message
from app.services.translation_pool import run_translation
from app.services.translator import translator
from app.services.clustering import ClusteringService
from app.services.ner_extractor import NERService


settings = get_settings()

DEFAULT_BATCH_SIZE = 200

logger = logging.getLogger(__name__)


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

    translations: list[tuple] = []
    if non_empty_rows:
        grouped: dict[tuple[str, str | None], list] = {}
        for row in non_empty_rows:
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
                (row.id, translated_text, detected_lang, target_lang, priority)
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

        if translations:
            translated_at = datetime.now(timezone.utc)
            processed_ids = []
            
            for message_id, translated_text, source_lang, target_lang, priority in translations:
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
                processed_ids.append(message_id)
                
            await db.commit()
            
            if processed_ids:
                try:
                    result = await db.execute(select(Message).where(Message.id.in_(processed_ids)))
                    messages = result.scalars().all()
                    
                    clustering_service = ClusteringService(db)
                    ner_service = NERService(db)
                    
                    count_clustered = 0
                    count_ner = 0
                    
                    for msg in messages:
                        is_relevant = await clustering_service.process_single_message(msg)
                        
                        if is_relevant:
                            count_clustered += 1
                            has_entities = await ner_service.extract_and_save(msg)
                            if has_entities:
                                count_ner += 1
                                
                    if count_clustered > 0:
                        await db.commit()
                        logger.info(f"Intelligence Pipeline: Clustered {count_clustered}, NER {count_ner} messages")
                        
                except Exception as e:
                    logger.error(f"Intelligence Pipeline failed: {e}")

