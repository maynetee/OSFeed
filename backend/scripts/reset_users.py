import asyncio
import logging
from sqlalchemy import text
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.channel import user_channels, Channel
from app.models.message import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reset_users():
    """
    Deletes all users from the database.
    
    Due to cascade deletion configurations:
    - entries in 'user_channels' will be deleted (ON DELETE CASCADE)
    - entries in 'channels' will REMAIN (no cascade from user side)
    - entries in 'messages' will REMAIN (linked to channels)
    """
    logger.info("Starting user reset process...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Check counts before
            user_count = await session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = user_count.scalar()
            
            channel_count = await session.execute(text("SELECT COUNT(*) FROM channels"))
            channel_count = channel_count.scalar()
            
            message_count = await session.execute(text("SELECT COUNT(*) FROM messages"))
            message_count = message_count.scalar()
            
            logger.info(f"BEFORE: Users={user_count}, Channels={channel_count}, Messages={message_count}")
            
            if user_count == 0:
                logger.info("No users to delete.")
                return

            # Delete all users
            logger.info("Deleting all users...")
            await session.execute(text("DELETE FROM users"))
            await session.commit()
            
            # Check counts after
            user_count_after = await session.execute(text("SELECT COUNT(*) FROM users"))
            user_count_after = user_count_after.scalar()
            
            channel_count_after = await session.execute(text("SELECT COUNT(*) FROM channels"))
            channel_count_after = channel_count_after.scalar()
            
            message_count_after = await session.execute(text("SELECT COUNT(*) FROM messages"))
            message_count_after = message_count_after.scalar()
            
            logger.info(f"AFTER: Users={user_count_after}, Channels={channel_count_after}, Messages={message_count_after}")
            
            if user_count_after == 0 and channel_count_after == channel_count and message_count_after == message_count:
                logger.info("SUCCESS: Users deleted, but Channels and Messages preserved.")
            else:
                logger.error("WARNING: Unexpected counts after deletion!")

        except Exception as e:
            logger.error(f"Error during reset: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(reset_users())
