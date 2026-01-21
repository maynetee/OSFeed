import asyncio
import logging
from app.database import init_db, AsyncSessionLocal
from app.models.user import User
from app.models.channel import Channel, user_channels
from app.models.summary import Summary 
from app.models.message import Message 
from app.models.collection import Collection
from app.models.fetch_job import FetchJob
from app.services.telegram_collector import get_shared_collector
from sqlalchemy import select, func, delete

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_shared_channels():
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # 1. Cleanup test data
        logger.info("Cleaning up test data...")
        await db.execute(delete(User).where(User.email.like('test_%@example.com')))
        await db.execute(delete(Channel).where(Channel.username == 'test_shared_channel'))
        await db.commit()

        # 2. Create 2 Users
        logger.info("Creating 2 test users...")
        user1 = User(email="test_1@example.com", hashed_password="hashed_pw", is_active=True)
        user2 = User(email="test_2@example.com", hashed_password="hashed_pw", is_active=True)
        db.add(user1)
        db.add(user2)
        await db.commit()
        await db.refresh(user1)
        await db.refresh(user2)

        # 3. User 1 adds Channel X
        logger.info("User 1 adding 'test_shared_channel'...")
        channel_name = "test_shared_channel"
        
        # Simulate "Add Channel" logic (check exists, if not create)
        result = await db.execute(select(Channel).where(Channel.username == channel_name))
        channel = result.scalars().first()
        
        if not channel:
            channel = Channel(username=channel_name, title="Test Channel")
            db.add(channel)
            await db.commit()
            await db.refresh(channel)
            
        # Link to User 1
        await db.execute(user_channels.insert().values(user_id=user1.id, channel_id=channel.id))
        await db.commit()

        # 4. User 2 adds SAME Channel X
        logger.info("User 2 adding 'test_shared_channel'...")
        result = await db.execute(select(Channel).where(Channel.username == channel_name))
        channel_existing = result.scalars().first()
        
        if channel_existing:
             # Link to User 2
            await db.execute(user_channels.insert().values(user_id=user2.id, channel_id=channel_existing.id))
            await db.commit()

        # 5. Verify Database State
        logger.info("Verifying database state...")
        
        # Check Channel Count
        channel_count = await db.execute(select(func.count(Channel.id)).where(Channel.username == channel_name))
        count_c = channel_count.scalar()
        
        # Check Link Count
        link_count = await db.execute(select(func.count()).select_from(user_channels).where(user_channels.c.channel_id == channel.id))
        count_l = link_count.scalar()

        logger.info(f"Channel Count (should be 1): {count_c}")
        logger.info(f"Link Count (should be 2): {count_l}")

        if count_c == 1 and count_l == 2:
            print("\nSUCCESS: Shared channel logic verified! 1 Channel shared by 2 Users.")
        else:
            print(f"\nFAILURE: Expected 1 Channel and 2 Links. Got {count_c} Channels and {count_l} Links.")

if __name__ == "__main__":
    asyncio.run(verify_shared_channels())
