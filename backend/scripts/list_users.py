import asyncio
import sys
import os

# Add the parent directory to sys.path to allow importing from 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.summary import Summary
from app.models.message import Message
from app.models.channel import Channel
from app.models.fetch_job import FetchJob
from app.models.collection import Collection
from app.models.collection_share import CollectionShare
from app.models.alert import Alert
from app.models.api_usage import ApiUsage
from app.models.audit_log import AuditLog
from sqlalchemy import select

async def list_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("No users found.")
            return

        print(f"{'ID':<40} | {'Email':<30} | {'Role':<10} | {'Full Name':<20}")
        print("-" * 110)
        for user in users:
            print(f"{str(user.id):<40} | {user.email:<30} | {user.role.value:<10} | {user.full_name or 'N/A':<20}")

if __name__ == "__main__":
    asyncio.run(list_users())
