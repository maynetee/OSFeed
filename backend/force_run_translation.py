import asyncio
import sys
import os
import logging
from sqlalchemy import select, func

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.jobs.translate_pending_messages import translate_pending_messages_job
from app.database import AsyncSessionLocal
# Import all models to ensure SQLAlchemy mappers are initialized
from app.models.message import Message
from app.models.channel import Channel
from app.models.fetch_job import FetchJob
from app.models.user import User
from app.models.collection import Collection
from app.models.summary import Summary
from app.models.alert import Alert
from app.models.api_usage import ApiUsage
from app.models.audit_log import AuditLog
from app.models.collection_share import CollectionShare

async def force_run():
    async with AsyncSessionLocal() as db:
         # Check count first
        count = (await db.execute(select(func.count(Message.id)).where(Message.needs_translation == True))).scalar()
        logger.info(f"Pending messages BEFORE run: {count}")

    logger.info("Starting forced translation job (batch=1000)...")
    try:
        await translate_pending_messages_job(batch_size=1000) 
        logger.info("Job completed successfully.")
    except Exception as e:
        logger.error(f"Job failed with error: {e}", exc_info=True)

    async with AsyncSessionLocal() as db:
         # Check count after
        count = (await db.execute(select(func.count(Message.id)).where(Message.needs_translation == True))).scalar()
        logger.info(f"Pending messages AFTER run: {count}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(force_run())
