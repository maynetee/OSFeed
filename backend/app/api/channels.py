from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.database import get_db, AsyncSessionLocal
from app.models.channel import Channel
from app.models.user import User
from app.schemas.channel import ChannelCreate, ChannelResponse
from app.services.telegram_collector import TelegramCollector
from app.auth.users import current_active_user
from app.services.audit import record_audit_event
from typing import List

router = APIRouter()


@router.post("", response_model=ChannelResponse)
async def add_channel(
    channel_data: ChannelCreate,
    user: User = Depends(current_active_user),
):
    """Add a new Telegram channel to follow.

    Requires authentication.
    """
    # Clean username - remove URL prefix if present
    username = channel_data.username.strip()
    if username.startswith("https://t.me/"):
        username = username.replace("https://t.me/", "")
    if username.startswith("t.me/"):
        username = username.replace("t.me/", "")
    username = username.lstrip("@")

    # First, fetch channel info from Telegram (BEFORE opening DB session)
    collector = TelegramCollector()
    try:
        channel_info = await collector.get_channel_info(username)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch channel: {str(e)}")
    finally:
        await collector.disconnect()

    # Now open DB session only for database operations (quick)
    async with AsyncSessionLocal() as db:
        try:
            # Check if channel already exists
            result = await db.execute(
                select(Channel).where(Channel.username == username)
            )
            existing_channel = result.scalar_one_or_none()

            if existing_channel:
                raise HTTPException(status_code=400, detail="Channel already exists")

            # Create new channel
            new_channel = Channel(
                telegram_id=channel_info['id'],
                username=username,
                title=channel_info['title'],
                description=channel_info.get('description', ''),
                subscriber_count=channel_info.get('participants_count', 0),
            )

            db.add(new_channel)
            record_audit_event(
                db,
                user_id=user.id,
                action="channel.create",
                resource_type="channel",
                resource_id=str(new_channel.id),
                metadata={"username": username},
            )
            await db.commit()
            await db.refresh(new_channel)

            return new_channel
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("", response_model=List[ChannelResponse])
async def list_channels(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all followed channels.

    Requires authentication.
    """
    result = await db.execute(select(Channel).where(Channel.is_active == True))
    channels = result.scalars().all()
    return channels


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a channel.

    Requires authentication.
    """
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Soft delete - just deactivate
    channel.is_active = False
    record_audit_event(
        db,
        user_id=user.id,
        action="channel.delete",
        resource_type="channel",
        resource_id=str(channel.id),
        metadata={"username": channel.username},
    )
    await db.commit()

    return {"message": "Channel deleted successfully"}
