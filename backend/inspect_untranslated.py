import asyncio
import sys
import os
from sqlalchemy import select, func, text

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import AsyncSessionLocal
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

async def inspect_db():
    async with AsyncSessionLocal() as db:
        # Count needs_translation=True
        result = await db.execute(
            select(func.count(Message.id)).where(Message.needs_translation == True)
        )
        count = result.scalar()
        print(f"Total messages needing translation: {count}")

        # Check sample of stuck messages
        stmt = (
            select(Message)
            .where(Message.needs_translation == True)
            .limit(5)
        )
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        print("\n--- Sample Pending Messages ---")
        for msg in messages:
            print(f"ID: {msg.id}")
            print(f"Text Preview: {msg.original_text[:30]}...")
            print(f"Is Duplicate: {msg.is_duplicate}")
            print(f"Published At: {msg.published_at}")
            print(f"Source Lang: {msg.source_language}")
            print(f"Translated Text: {msg.translated_text}")
            print(f"Fetched At: {msg.fetched_at}")
            print("-------------------------------")

        # Check if any messages have needs_translation=False but NO translated text (skipped?)
        # And are NOT duplicates (because duplicates usually have no text)
        stmt_skipped = (
            select(Message)
            .where(Message.needs_translation == False)
            .where(Message.translated_text == None)
            .where(Message.is_duplicate == False)
            .limit(5)
        )
        result = await db.execute(stmt_skipped)
        skipped = result.scalars().all()
        
        print("\n--- Sample Skipped/Failed Messages (No Translation, Marked Done, Not Duplicate) ---")
        for msg in skipped:
            print(f"ID: {msg.id}")
            print(f"Text Preview: {msg.original_text[:30]}...")
            print(f"Priority: {msg.translation_priority}")
            print(f"Source Lang: {msg.source_language}")
            print("-------------------------------")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(inspect_db())
