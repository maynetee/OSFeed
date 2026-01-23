from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, insert, delete
from sqlalchemy.orm import selectinload
from uuid import UUID
import logging

from app.database import get_db, AsyncSessionLocal
from app.models.channel import Channel, user_channels
from app.models.fetch_job import FetchJob
from app.models.collection import Collection
from app.models.user import User
from app.schemas.channel import ChannelCreate, ChannelResponse
from app.services.fetch_queue import enqueue_fetch_job
import re
from app.auth.users import current_active_user
from app.services.audit import record_audit_event
from app.services.telegram_client import get_telegram_client
from app.services.channel_join_queue import queue_channel_join
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.fetch_job import FetchJobStatus
from app.utils.response_cache import response_cache
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class RefreshChannelsRequest(BaseModel):
    channel_ids: Optional[List[UUID]] = None


class RefreshChannelsResponse(BaseModel):
    job_ids: List[UUID]


class FetchJobsStatusRequest(BaseModel):
    job_ids: List[UUID]


class FetchJobsStatusResponse(BaseModel):
    jobs: List[FetchJobStatus]


async def _get_latest_fetch_jobs(db: AsyncSession, channel_ids: list[UUID]) -> dict[UUID, FetchJob]:
    if not channel_ids:
        return {}
    latest_subquery = (
        select(
            FetchJob.channel_id,
            func.max(FetchJob.created_at).label("max_created_at"),
        )
        .where(FetchJob.channel_id.in_(channel_ids))
        .group_by(FetchJob.channel_id)
        .subquery()
    )

    result = await db.execute(
        select(FetchJob).join(
            latest_subquery,
            and_(
                FetchJob.channel_id == latest_subquery.c.channel_id,
                FetchJob.created_at == latest_subquery.c.max_created_at,
            ),
        )
    )
    jobs = result.scalars().all()
    return {job.channel_id: job for job in jobs}


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

    # Fix regex: remove double escaping and ensure correct pattern
    if not re.match(r"^[a-zA-Z][\w\d]{3,30}[a-zA-Z\d]$", username):
        raise HTTPException(status_code=400, detail="Invalid Telegram username format. Must be 5-32 chars, start with letter.")

    # Telegram integration has been removed - only allow linking to existing channels
    async with AsyncSessionLocal() as db:
        try:
            # Check if channel already exists
            result = await db.execute(
                select(Channel).where(Channel.username == username)
            )
            existing_channel = result.scalar_one_or_none()

            channel_to_use = None
            is_new = False

            if existing_channel:
                # Check if user already has this channel
                link_result = await db.execute(
                    select(user_channels).where(
                        and_(
                            user_channels.c.user_id == user.id,
                            user_channels.c.channel_id == existing_channel.id
                        )
                    )
                )
                existing_link = link_result.first()
                
                if existing_link:
                    # If already linked but inactive, reactivate it? 
                    # Usually if linked, it should be active for this user.
                    if not existing_channel.is_active:
                         existing_channel.is_active = True
                         await db.commit()
                         # We still inform the user it was already there, but now active.
                         pass
                    else:
                        raise HTTPException(status_code=400, detail="Channel already exists in your list")
                
                # If channel exists (inactive or active) but NOT linked:
                if not existing_channel.is_active:
                    existing_channel.is_active = True
                    
                # Link user to existing channel
                # (Only if not already linked - logic above covers linked case)
                if not existing_link:
                    await db.execute(
                        insert(user_channels).values(
                            user_id=user.id,
                            channel_id=existing_channel.id
                        )
                    )

                channel_to_use = existing_channel
            else:
                # Channel doesn't exist - create via Telegram
                telegram_client = get_telegram_client()

                # Check JoinChannel limit before proceeding
                if not await telegram_client.can_join_channel():
                    if settings.telegram_join_channel_queue_enabled:
                        # Queue for later processing
                        await queue_channel_join(username, user.id)
                        raise HTTPException(
                            status_code=202,
                            detail="Daily channel join limit reached. Your request has been queued."
                        )
                    else:
                        raise HTTPException(
                            status_code=429,
                            detail="Daily channel join limit reached. Please try again tomorrow."
                        )

                try:
                    # Resolve and join channel via Telegram
                    channel_info = await telegram_client.resolve_channel(username)
                    await telegram_client.join_public_channel(username)
                    await telegram_client.record_channel_join()

                    # Create new channel record
                    channel_to_use = Channel(
                        username=username,
                        telegram_id=channel_info['telegram_id'],
                        title=channel_info['title'],
                        description=channel_info.get('description'),
                        is_active=True
                    )
                    db.add(channel_to_use)
                    is_new = True

                except ValueError as e:
                    # Invalid username, private channel, etc.
                    raise HTTPException(status_code=400, detail=str(e))

            # Assign to collections (for both new and existing linked channels)
            collections_result = await db.execute(
                select(Collection)
                .options(selectinload(Collection.channels))
                .where(Collection.user_id == user.id)
            )
            collections = collections_result.scalars().all()
            
            # Re-check collections for the user
            channel_lang = channel_to_use.detected_language
            search_text = f"{channel_to_use.title} {channel_to_use.description or ''}".lower()
            
            for collection in collections:
                # Check if already in collection to avoid dupes
                if channel_to_use in collection.channels:
                    continue

                if collection.is_global:
                    continue
                if collection.is_default:
                    collection.channels.append(channel_to_use)
                    continue
                if collection.auto_assign_languages and channel_lang:
                    if channel_lang in (collection.auto_assign_languages or []):
                        collection.channels.append(channel_to_use)
                        continue
                if collection.auto_assign_keywords:
                    if any(keyword.lower() in search_text for keyword in collection.auto_assign_keywords or []):
                        collection.channels.append(channel_to_use)
                        continue
                if collection.auto_assign_tags and channel_to_use.tags:
                    if any(tag in (collection.auto_assign_tags or []) for tag in channel_to_use.tags):
                        collection.channels.append(channel_to_use)

            record_audit_event(
                db,
                user_id=user.id,
                action="channel.create" if is_new else "channel.link",
                resource_type="channel",
                resource_id=str(channel_to_use.id),
                metadata={"username": username, "is_new": is_new},
            )
            await db.commit()
            await db.refresh(channel_to_use)

            # Enqueue fetch job (enqueue_fetch_job handles deduplication if already running)
            job = await enqueue_fetch_job(channel_to_use.id, channel_to_use.username, days=7)

            response = ChannelResponse.model_validate(channel_to_use).model_dump()
            if job:
                response["fetch_job"] = FetchJobStatus.model_validate(job).model_dump()
            else:
                response["fetch_job"] = None
                
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Error adding channel")
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("", response_model=List[ChannelResponse])
async def list_channels(
    request: Request,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all followed channels.

    Requires authentication.
    """
    # Filter by user linkage
    result = await db.execute(
        select(Channel)
        .join(user_channels, Channel.id == user_channels.c.channel_id)
        .where(
            and_(
                user_channels.c.user_id == user.id,
                Channel.is_active == True
            )
        )
    )
    channels = result.scalars().all()
    job_map = await _get_latest_fetch_jobs(db, [channel.id for channel in channels])

    response = []
    for channel in channels:
        data = ChannelResponse.model_validate(channel).model_dump()
        job = job_map.get(channel.id)
        data["fetch_job"] = FetchJobStatus.model_validate(job).model_dump() if job else None
        response.append(data)
    return response


@router.post("/refresh", response_model=RefreshChannelsResponse)
async def refresh_channels(
    payload: RefreshChannelsRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger fetch jobs for active channels the user follows."""
    channel_ids = payload.channel_ids or []
    query = (
        select(Channel)
        .join(user_channels, Channel.id == user_channels.c.channel_id)
        .where(
            and_(
                user_channels.c.user_id == user.id,
                Channel.is_active == True,
            )
        )
    )
    if channel_ids:
        query = query.where(Channel.id.in_(channel_ids))

    result = await db.execute(query)
    channels = result.scalars().all()

    job_ids: list[UUID] = []
    for channel in channels:
        job = await enqueue_fetch_job(channel.id, channel.username, days=7)
        if job:
            job_ids.append(job.id)

    return RefreshChannelsResponse(job_ids=job_ids)


@router.post("/fetch-jobs/status", response_model=FetchJobsStatusResponse)
async def fetch_jobs_status(
    payload: FetchJobsStatusRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Return statuses for requested fetch jobs owned by the user."""
    if not payload.job_ids:
        return FetchJobsStatusResponse(jobs=[])

    result = await db.execute(
        select(FetchJob)
        .join(Channel, FetchJob.channel_id == Channel.id)
        .join(user_channels, Channel.id == user_channels.c.channel_id)
        .where(
            and_(
                user_channels.c.user_id == user.id,
                FetchJob.id.in_(payload.job_ids),
            )
        )
    )
    jobs = result.scalars().all()
    return FetchJobsStatusResponse(jobs=[FetchJobStatus.model_validate(job) for job in jobs])


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    request: Request,
    channel_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single channel by ID.

    Requires authentication.
    """
    result = await db.execute(
        select(Channel).where(Channel.id == channel_id, Channel.is_active == True)
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    job_map = await _get_latest_fetch_jobs(db, [channel.id])
    data = ChannelResponse.model_validate(channel).model_dump()
    job = job_map.get(channel.id)
    data["fetch_job"] = FetchJobStatus.model_validate(job).model_dump() if job else None
    return data


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a channel.

    Requires authentication.
    """
    # Verify channel exists
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Unlink user from channel
    # This preserves the channel for other users who might use it
    await db.execute(
        delete(user_channels).where(
            and_(
                user_channels.c.user_id == user.id,
                user_channels.c.channel_id == channel_id
            )
        )
    )
    
    # Optional: If no users are left, we could potentially deactivate it,
    # but for now, we leave it active for simplicity or background cleanup.

    record_audit_event(
        db,
        user_id=user.id,
        action="channel.delete",
        resource_type="channel",
        resource_id=str(channel.id),
        metadata={"username": channel.username},
    )
    await db.commit()

    return {"message": "Channel removed successfully"}
