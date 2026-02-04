from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, insert, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import selectinload
from uuid import UUID
import logging

from app.database import get_db
from app.models.channel import Channel, user_channels
from app.models.fetch_job import FetchJob
from app.models.collection import Collection
from app.models.user import User
from app.schemas.channel import ChannelCreate, ChannelResponse, BulkChannelCreate, BulkChannelResponse, BulkChannelFailure
from app.services.fetch_queue import enqueue_fetch_job
import re
from app.auth.users import current_active_user
from app.services.audit import record_audit_event
from app.services.telegram_client import get_telegram_client
from app.services.channel_join_queue import queue_channel_join
from app.services.translation_service import invalidate_channel_translation_cache
from app.services import channel_utils
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
    db: AsyncSession = Depends(get_db),
):
    """Add a new Telegram channel to the authenticated user's follow list.

    Validates the Telegram username format (5-32 characters, must start with a letter),
    creates or retrieves the channel record, links it to the user, and enqueues a background
    fetch job to retrieve recent messages.

    Requires authentication. Users can only add channels to their own follow list.

    Args:
        channel_data: Channel creation data containing the Telegram username to follow.
        user: The authenticated user (injected via dependency).
        db: Database session (injected via dependency).

    Returns:
        ChannelResponse containing the channel details and initial fetch job status.

    Raises:
        HTTPException(400): If the username format is invalid.
        HTTPException(409): If the user already follows this channel.
        HTTPException(500): If a database or Telegram API error occurs.
    """
    # Clean and validate username
    username = channel_utils.clean_channel_username(channel_data.username)

    if not channel_utils.validate_channel_username(username):
        raise HTTPException(status_code=400, detail="Invalid Telegram username format. Must be 5-32 chars, start with letter.")

    # Use shared channel add logic
    result = await channel_utils.process_channel_add(
        db=db,
        user_id=user.id,
        username=username,
        error_mode="raise"
    )

    # Commit the transaction
    await db.commit()
    await db.refresh(result['channel'])

    # Build response
    response = ChannelResponse.model_validate(result['channel']).model_dump()
    response["fetch_job"] = result['job']

    return response


@router.post("/bulk", response_model=BulkChannelResponse)
async def add_channels_bulk(
    bulk_data: BulkChannelCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Add multiple Telegram channels to the user's follow list in a single request.

    Processes channels sequentially to respect Telegram API rate limits. Each channel
    is validated, created or retrieved, and linked to the user. Invalid usernames or
    duplicate channels are reported in the failed array without stopping the operation.

    Returns partial results - some channels may succeed while others fail. All successful
    additions are committed together at the end.

    Requires authentication. Users can only add channels to their own follow list.

    Args:
        bulk_data: Bulk creation data containing a list of Telegram usernames to follow.
        user: The authenticated user (injected via dependency).
        db: Database session (injected via dependency).

    Returns:
        BulkChannelResponse with:
        - succeeded: List of successfully added channels with their details and fetch jobs.
        - failed: List of failed additions with username and error message.
        - total: Total number of channels attempted.
        - success_count: Number of successfully added channels.
        - failure_count: Number of failed channel additions.
    """
    succeeded: List[ChannelResponse] = []
    failed: List[BulkChannelFailure] = []

    if not bulk_data.usernames:
        return BulkChannelResponse(
            succeeded=[],
            failed=[],
            total=0,
            success_count=0,
            failure_count=0,
        )

    for raw_username in bulk_data.usernames:
        # Clean and validate username
        username = channel_utils.clean_channel_username(raw_username)
        if not username:
            continue

        if not channel_utils.validate_channel_username(username):
            failed.append(BulkChannelFailure(
                username=raw_username,
                error="Invalid Telegram username format. Must be 5-32 chars, start with letter."
            ))
            continue

        # Use shared channel add logic
        result = await channel_utils.process_channel_add(
            db=db,
            user_id=user.id,
            username=username,
            error_mode="return"
        )

        if not result['success']:
            # Add to failed list
            failed.append(BulkChannelFailure(
                username=raw_username,
                error=result['error']
            ))
            continue

        # Success - prepare response
        channel_to_use = result['channel']

        # Flush to get the channel ID for the response
        await db.flush()
        await db.refresh(channel_to_use)

        # Invalidate translation cache since user-channel association changed
        await invalidate_channel_translation_cache(channel_to_use.id)

        # Build response
        response = ChannelResponse.model_validate(channel_to_use).model_dump()
        response["fetch_job"] = result['job']

        succeeded.append(ChannelResponse.model_validate(response))

    # Commit all successful changes
    await db.commit()

    return BulkChannelResponse(
        succeeded=succeeded,
        failed=failed,
        total=len(bulk_data.usernames),
        success_count=len(succeeded),
        failure_count=len(failed),
    )


@router.get("", response_model=List[ChannelResponse])
@response_cache(expire=60, namespace="channels-list")
async def list_channels(
    request: Request,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active Telegram channels followed by the authenticated user.

    Returns channels the user has added to their follow list, including details about
    each channel (title, description, subscriber count, etc.) and the status of the
    most recent fetch job for each channel.

    Results are cached for 60 seconds per user to improve performance.

    Requires authentication. Users can only see their own followed channels.

    Args:
        request: The FastAPI request object (used for cache key generation).
        user: The authenticated user (injected via dependency).
        db: Database session (injected via dependency).

    Returns:
        List of ChannelResponse objects, each containing:
        - Channel details (id, username, title, description, subscriber_count, etc.)
        - fetch_job: Status of the most recent fetch job (or None if no jobs exist).
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
    """Trigger background fetch jobs to retrieve recent messages from followed channels.

    Enqueues fetch jobs for the specified channels (or all user's channels if none specified).
    Each job retrieves messages from the last 7 days. Jobs are processed asynchronously by
    background workers.

    Requires authentication. Users can only trigger fetch jobs for channels they follow.

    Args:
        payload: Request payload optionally containing a list of channel IDs to refresh.
                If channel_ids is empty or None, all user's active channels are refreshed.
        user: The authenticated user (injected via dependency).
        db: Database session (injected via dependency).

    Returns:
        RefreshChannelsResponse containing:
        - job_ids: List of UUIDs for the created fetch jobs that can be used to poll status.
    """
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


class RefreshInfoRequest(BaseModel):
    channel_ids: Optional[List[UUID]] = None


class ChannelInfoUpdate(BaseModel):
    channel_id: UUID
    subscriber_count: int
    title: str
    success: bool
    error: Optional[str] = None


class RefreshInfoResponse(BaseModel):
    results: List[ChannelInfoUpdate]


@router.post("/refresh-info", response_model=RefreshInfoResponse)
async def refresh_channel_info(
    payload: RefreshInfoRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update channel metadata from Telegram without fetching historical messages.

    Queries Telegram API for updated channel information (title, description, subscriber count)
    and updates the local database. This is a lightweight operation compared to a full message
    fetch, useful for keeping channel metadata current.

    Processes channels synchronously and reports individual success/failure for each channel.

    Requires authentication. Users can only refresh info for channels they follow.

    Args:
        payload: Request payload optionally containing a list of channel IDs to refresh.
                If channel_ids is empty or None, all user's active channels are updated.
        user: The authenticated user (injected via dependency).
        db: Database session (injected via dependency).

    Returns:
        RefreshInfoResponse containing:
        - results: List of ChannelInfoUpdate objects for each processed channel, including:
          - channel_id: UUID of the channel.
          - subscriber_count: Updated subscriber count.
          - title: Updated channel title.
          - success: Whether the update succeeded.
          - error: Error message if the update failed (None on success).
    """
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

    telegram_client = get_telegram_client()
    results = []

    for channel in channels:
        try:
            channel_info = await telegram_client.resolve_channel(channel.username)
            channel.title = channel_info.get('title') or channel.title
            channel.description = channel_info.get('description') or channel.description
            channel.subscriber_count = channel_info.get('subscribers', 0)

            results.append(ChannelInfoUpdate(
                channel_id=channel.id,
                subscriber_count=channel.subscriber_count,
                title=channel.title,
                success=True
            ))
            logger.info(f"Updated info for {channel.username}: {channel.subscriber_count} subscribers")
        except (SQLAlchemyError, IntegrityError) as e:
            logger.error(f"Database error refreshing info for {channel.username} (user {user.id}): {type(e).__name__}: {e}", exc_info=True)
            results.append(ChannelInfoUpdate(
                channel_id=channel.id,
                subscriber_count=channel.subscriber_count,
                title=channel.title,
                success=False,
                error="Failed to refresh channel information due to database error."
            ))
        except ValueError as e:
            logger.debug(f"Channel error refreshing info for {channel.username} (user {user.id}): {e}")
            results.append(ChannelInfoUpdate(
                channel_id=channel.id,
                subscriber_count=channel.subscriber_count,
                title=channel.title,
                success=False,
                error="Failed to refresh channel information. Channel may be invalid or private."
            ))
        except RuntimeError as e:
            logger.error(f"Telegram client error refreshing info for {channel.username} (user {user.id}): {e}")
            results.append(ChannelInfoUpdate(
                channel_id=channel.id,
                subscriber_count=channel.subscriber_count,
                title=channel.title,
                success=False,
                error="Failed to refresh channel information due to connection error."
            ))

    await db.commit()
    return RefreshInfoResponse(results=results)


@router.post("/fetch-jobs/status", response_model=FetchJobsStatusResponse)
async def fetch_jobs_status(
    payload: FetchJobsStatusRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the current status of background fetch jobs for the user's channels.

    Polls the status of one or more fetch jobs by their IDs. Useful for tracking progress
    after triggering a channel refresh. Only returns jobs for channels the user follows
    to prevent information leakage.

    Requires authentication. Users can only query fetch jobs for their own channels.

    Args:
        payload: Request payload containing a list of fetch job IDs to query.
        user: The authenticated user (injected via dependency).
        db: Database session (injected via dependency).

    Returns:
        FetchJobsStatusResponse containing:
        - jobs: List of FetchJobStatus objects with details about each job:
          - id: Job UUID.
          - status: Current status (pending, running, completed, failed).
          - created_at: When the job was created.
          - started_at: When the job started processing (None if not started).
          - completed_at: When the job completed (None if not completed).
          - error_message: Error details if the job failed (None on success).
    """
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
@response_cache(expire=60, namespace="channels-detail")
async def get_channel(
    request: Request,
    channel_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed information about a specific channel by its ID.

    Returns comprehensive channel details including metadata (title, description,
    subscriber count) and the status of the most recent fetch job.

    Results are cached for 60 seconds per user to improve performance.

    Requires authentication. Users can only retrieve details for channels they follow.

    Args:
        request: The FastAPI request object (used for cache key generation).
        channel_id: UUID of the channel to retrieve.
        user: The authenticated user (injected via dependency).
        db: Database session (injected via dependency).

    Returns:
        ChannelResponse containing:
        - Channel details (id, username, title, description, subscriber_count, etc.)
        - fetch_job: Status of the most recent fetch job (or None if no jobs exist).

    Raises:
        HTTPException(404): If the channel is not found or user doesn't follow it.
    """
    result = await db.execute(
        select(Channel)
        .join(user_channels, Channel.id == user_channels.c.channel_id)
        .where(
            and_(
                user_channels.c.user_id == user.id,
                Channel.id == channel_id,
                Channel.is_active == True
            )
        )
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
    """Unfollow a channel by removing it from the user's follow list.

    Removes the association between the user and the channel. The channel record itself
    is preserved in the database for other users who may still follow it. An audit event
    is recorded for this action.

    Requires authentication. Users can only unfollow channels from their own follow list.

    Args:
        channel_id: UUID of the channel to unfollow.
        user: The authenticated user (injected via dependency).
        db: Database session (injected via dependency).

    Returns:
        JSON response with a success message.

    Raises:
        HTTPException(404): If the channel is not found or user doesn't follow it.
    """
    # Verify channel exists and user has access (single query to prevent enumeration)
    result = await db.execute(
        select(Channel)
        .join(user_channels, Channel.id == user_channels.c.channel_id)
        .where(
            and_(
                user_channels.c.user_id == user.id,
                Channel.id == channel_id
            )
        )
    )
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
