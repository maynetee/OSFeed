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
from app.services.telegram_collector import get_channel_info_with_lock
import re
from app.auth.users import current_active_user
from app.services.audit import record_audit_event
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

    # Check database first to avoid unnecessary Telegram calls
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
                # Channel doesn't exist by username, need to fetch from Telegram
                try:
                    channel_info = await get_channel_info_with_lock(username)
                except Exception as exc:
                    error_msg = str(exc).lower()
                    if "usernameinvalid" in error_msg or "usernamenotoccupied" in error_msg:
                        raise HTTPException(status_code=400, detail="Channel not found on Telegram")
                    elif "channelprivate" in error_msg:
                        raise HTTPException(status_code=400, detail="This is a private channel")
                    else:
                        raise HTTPException(status_code=400, detail=f"Invalid Telegram channel: {exc}")

                # Check if channel exists by Telegram ID (to handle username changes or casing mismatches)
                tid = channel_info.get("id")
                if tid:
                    result = await db.execute(select(Channel).where(Channel.telegram_id == tid))
                    existing_by_id = result.scalar_one_or_none()
                    
                    if existing_by_id:
                        # Found by ID! Update it and use it.
                        existing_by_id.username = channel_info.get("username") or existing_by_id.username
                        existing_by_id.title = channel_info.get("title") or existing_by_id.title
                        existing_by_id.description = channel_info.get("description") or existing_by_id.description
                        existing_by_id.subscriber_count = channel_info.get("participants_count") or existing_by_id.subscriber_count
                        
                        if not existing_by_id.is_active:
                             existing_by_id.is_active = True
                        
                        channel_to_use = existing_by_id
                        
                        # Check if already linked (logic similar to above, but we are in the 'else' of username check)
                        # We need to ensure we link it.
                        link_result = await db.execute(
                            select(user_channels).where(
                                and_(
                                    user_channels.c.user_id == user.id,
                                    user_channels.c.channel_id == existing_by_id.id
                                )
                            )
                        )
                        if link_result.first():
                             # Already linked.
                             pass
                        else:
                             await db.execute(
                                insert(user_channels).values(
                                    user_id=user.id,
                                    channel_id=existing_by_id.id
                                )
                            )
                        is_new = False
                    else:
                         # Truly new
                        new_channel = Channel(
                            telegram_id=tid,
                            username=channel_info.get("username") or username,
                            title=channel_info.get("title") or username,
                            description=channel_info.get("description") or '',
                            subscriber_count=channel_info.get("participants_count") or 0,
                        )
                        db.add(new_channel)
                        await db.flush() # Get ID

                        # Link user validation
                        await db.execute(
                            insert(user_channels).values(
                                user_id=user.id,
                                channel_id=new_channel.id
                            )
                        )
                        
                        channel_to_use = new_channel
                        is_new = True
                else:
                    # Should unlikely occur if fetch succeeded but no ID?
                    # Fallback to create if no ID returned (flimsy but safeguard)
                    new_channel = Channel(
                        telegram_id=None,
                        username=channel_info.get("username") or username,
                        title=channel_info.get("title") or username,
                        description=channel_info.get("description") or '',
                        subscriber_count=channel_info.get("participants_count") or 0,
                    )
                    db.add(new_channel)
                    await db.flush()

                    await db.execute(
                        insert(user_channels).values(
                            user_id=user.id,
                            channel_id=new_channel.id
                        )
                    )
                    channel_to_use = new_channel
                    is_new = True

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
