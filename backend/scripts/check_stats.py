import asyncio
import logging
from sqlalchemy import text
from app.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_stats():
    """
    Simple script to check counts of Users, Channels, and Messages.
    """
    async with AsyncSessionLocal() as session:
        try:
            user_count = await session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = user_count.scalar()
            
            channel_count = await session.execute(text("SELECT COUNT(*) FROM channels"))
            channel_count = channel_count.scalar()
            
            message_count = await session.execute(text("SELECT COUNT(*) FROM messages"))
            message_count = message_count.scalar()
            
            print(f"STATS: Users={user_count}, Channels={channel_count}, Messages={message_count}")
            
        except Exception as e:
            logger.error(f"Error checking stats: {e}")

if __name__ == "__main__":
    asyncio.run(check_stats())
