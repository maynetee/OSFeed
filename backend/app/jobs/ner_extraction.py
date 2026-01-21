import logging
from sqlalchemy import select, and_, or_
from app.database import AsyncSessionLocal
from app.models.message import Message
from app.services.ner_extractor import NERService

logger = logging.getLogger(__name__)

async def run_ner_job():
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(Message).where(
                and_(
                    Message.translated_text.isnot(None),
                    or_(
                        Message.entities.is_(None),
                    )
                )
            ).limit(50)
            
            result = await session.execute(stmt)
            messages = result.scalars().all()
            
            if not messages:
                return

            service = NERService(session)
            count = 0
            
            for message in messages:
                if message.entities and (message.entities.get("LOC") or message.entities.get("ORG")):
                     continue
                     
                found = await service.extract_and_save(message)
                if found:
                    count += 1
            
            await session.commit()
            
            if count > 0:
                logger.info(f"NER Job: Extracted entities for {count} messages")
                
        except Exception as e:
            logger.error(f"NER job failed: {e}", exc_info=True)
