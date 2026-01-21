
import asyncio
import os
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.fetch_job import FetchJob
from app.models.channel import Channel
from app.models.message import Message
from app.models.user import User
from app.models.collection import Collection
from app.models.summary import Summary
from app.models.api_usage import ApiUsage

# Mock env vars if needed or rely on .env loading
# (Assuming the app runs with .env loaded)

async def main():
    async with AsyncSessionLocal() as db:
        # Find channel
        result = await db.execute(select(Channel).where(Channel.username.ilike('%Indy%')))
        channel = result.scalars().first()
        
        if not channel:
            print("Channel not found matching '%Indy%'")
            return

        print(f"Channel: {channel.username} (ID: {channel.id})")
        print(f"Is Active: {channel.is_active}")
        
        # Get jobs
        jobs_result = await db.execute(
            select(FetchJob)
            .where(FetchJob.channel_id == channel.id)
            .order_by(FetchJob.created_at.desc())
        )
        jobs = jobs_result.scalars().all()[:1]
        
        print(f"Found {len(jobs)} jobs:")
        for job in jobs:
            print(f"Job ID: {job.id}")
            print(f"  Status: {job.status}")
            print(f"  Stage: {job.stage}")
            print(f"  Error: {job.error_message}")
            print(f"  Created: {job.created_at}")
            print(f"  Finished: {job.finished_at}")

if __name__ == "__main__":
    asyncio.run(main())
