from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update, or_, tuple_, insert, and_, literal
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import selectinload
from uuid import UUID
import asyncio
import json

from app.database import get_db, AsyncSessionLocal
from app.models.message import Message, MessageTranslation
from app.utils.response_cache import response_cache
from app.utils.pagination import encode_cursor, decode_cursor
from app.models.channel import Channel
from app.models.user import User
from app.schemas.message import MessageResponse, MessageListResponse, SimilarMessagesResponse
from app.services.translation_pool import run_translation
from app.services.translator import translator
from app.services.message_utils import (
    message_to_response,
    apply_message_filters,
    get_similar_messages as get_similar_messages_service,
    get_single_message,
)
from app.services.message_streaming_service import create_message_stream
from app.services.message_export_service import (
    export_messages_csv as service_export_messages_csv,
    export_messages_html as service_export_messages_html,
    export_messages_pdf as service_export_messages_pdf,
)
from app.services.message_translation_bulk_service import translate_messages_batch, translate_single_message
from app.services.message_media_service import get_media_stream
from app.services.channel_utils import get_authorized_channel
from app.config import get_settings
from app.services.fetch_queue import enqueue_fetch_job
from app.auth.users import current_active_user
from app.services.cache import get_redis_client
from app.services.events import publish_message_translated
from app.services.audit import record_audit_event
from datetime import datetime, timezone
from typing import Optional
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()


@router.get("", response_model=MessageListResponse)
@response_cache(expire=60, namespace="messages-list")
async def list_messages(
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    cursor: Optional[str] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    media_types: Optional[list[str]] = Query(None),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve paginated message feed with flexible filtering and cursor-based pagination.

    Supports filtering by channel(s), date range, and media types. Uses cursor-based
    pagination for efficient scrolling through large datasets. Results are cached for 60 seconds.
    """
    query = select(Message).options(selectinload(Message.channel))
    query = apply_message_filters(query, user.id, channel_id, channel_ids, start_date, end_date, media_types)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(desc(Message.published_at), desc(Message.id))
    if cursor:
        cursor_published_at, cursor_id = decode_cursor(cursor)
        query = query.where(tuple_(Message.published_at, Message.id) < (cursor_published_at, cursor_id))
    else:
        query = query.offset(offset)
    query = query.limit(limit)
    result = await db.execute(query)
    messages = result.scalars().all()

    next_cursor = None
    if messages:
        last_message = messages[-1]
        next_cursor = encode_cursor(last_message.published_at, last_message.id)

    return MessageListResponse(
        messages=[message_to_response(message) for message in messages],
        total=total,
        page=offset // limit + 1 if not cursor else 1,
        page_size=limit,
        next_cursor=next_cursor,
    )


@router.get("/stream")
async def stream_messages(
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    batch_size: int = Query(20, ge=1, le=100),
    limit: int = Query(200, ge=1, le=1000),
    realtime: bool = Query(False),
    media_types: Optional[list[str]] = Query(None),
    user: User = Depends(current_active_user),
):
    """Stream messages via Server-Sent Events (SSE) with optional real-time updates.

    Returns messages in configurable batches. When realtime=true, uses Redis Pub/Sub
    to push new messages as they arrive. Ideal for live feed implementations.
    """
    return StreamingResponse(
        create_message_stream(
            user_id=user.id,
            channel_id=channel_id,
            channel_ids=channel_ids,
            start_date=start_date,
            end_date=end_date,
            batch_size=batch_size,
            limit=limit,
            realtime=realtime,
            media_types=media_types,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/search", response_model=MessageListResponse)
@response_cache(expire=60, namespace="messages-search")
async def search_messages(
    q: str = Query(..., min_length=3),
    channel_ids: Optional[list[UUID]] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    cursor: Optional[str] = Query(None),
    media_types: Optional[list[str]] = Query(None),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Search messages using case-insensitive full-text matching across original and translated text.

    Searches both original_text and translated_text fields. Supports filtering by channels,
    date ranges, and media types. Results are paginated and cached for 60 seconds.
    """
    try:
        search_term = f"%{q}%"
        search_filter = or_(
            Message.original_text.ilike(search_term),
            Message.translated_text.ilike(search_term),
        )
        query = select(Message).options(selectinload(Message.channel)).where(search_filter)
        query = apply_message_filters(query, user.id, None, channel_ids, start_date, end_date, media_types)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(desc(Message.published_at), desc(Message.id))
        if cursor:
            cursor_published_at, cursor_id = decode_cursor(cursor)
            query = query.where(tuple_(Message.published_at, Message.id) < (cursor_published_at, cursor_id))
        else:
            query = query.offset(offset)
        query = query.limit(limit)
        result = await db.execute(query)
        messages = result.scalars().all()

        next_cursor = None
        if messages:
            last_message = messages[-1]
            next_cursor = encode_cursor(last_message.published_at, last_message.id)

        return MessageListResponse(
            messages=[message_to_response(message) for message in messages],
            total=total,
            page=offset // limit + 1 if not cursor else 1,
            page_size=limit,
            next_cursor=next_cursor,
        )
    except HTTPException:
        raise
    except (SQLAlchemyError, IntegrityError) as e:
        logger.error(f"Database error searching messages for user {user.id}: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="MESSAGE_SEARCH_DATABASE_ERROR")
    except Exception as e:
        logger.error(f"Unexpected error searching messages for user {user.id}: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="MESSAGE_SEARCH_ERROR")


@router.post("/fetch-historical/{channel_id}")
async def fetch_historical_messages(
    channel_id: UUID,
    days: int = Query(7, ge=0, le=3650),
    user: User = Depends(current_active_user),
):
    """Enqueue a background job to fetch historical messages from Telegram for a specific channel.

    Queues an asynchronous fetch operation for the specified number of days (0 = all history).
    Requires user authorization for the channel. Returns a job_id for tracking progress.
    """
    async with AsyncSessionLocal() as db:
        channel = await get_authorized_channel(db, channel_id, user.id)

        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found or access denied")

    job = await enqueue_fetch_job(channel_id, channel.username, days)
    if days == 0:
        return {"message": "Queued fetch for all available history", "job_id": str(job.id)}
    return {"message": f"Queued fetch for last {days} days", "job_id": str(job.id)}


@router.post("/translate")
async def translate_messages(
    target_language: str = Query(..., description="Target language code"),
    channel_id: Optional[UUID] = None,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Batch re-translate messages to a new target language with audit logging.

    Translates all messages (or messages from a specific channel if channel_id provided)
    to the specified target language. Creates an audit trail and returns translation statistics.
    """
    # Record audit event
    record_audit_event(
        db=db,
        user_id=user.id,
        action="message.translate.batch",
        resource_type="message",
        resource_id=str(channel_id) if channel_id else None,
        metadata={
            "target_language": target_language,
            "channel_id": str(channel_id) if channel_id else None,
        },
    )

    result = await translate_messages_batch(
        user_id=user.id,
        target_language=target_language,
        channel_id=channel_id,
    )

    return result


@router.get("/export/csv")
async def export_messages_csv(
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    media_types: Optional[list[str]] = Query(None),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Export filtered messages to CSV format with audit logging.

    Generates a streaming CSV download of messages matching the specified filters.
    Includes channel information, timestamps, and both original and translated text.
    """
    record_audit_event(
        db=db,
        user_id=user.id,
        action="message.export.csv",
        resource_type="message",
        resource_id=str(channel_id) if channel_id else None,
        metadata={
            "format": "csv",
            "channel_id": str(channel_id) if channel_id else None,
            "channel_ids": [str(cid) for cid in channel_ids] if channel_ids else None,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "media_types": media_types,
        },
    )

    filename = "osfeed-messages.csv"
    return StreamingResponse(
        service_export_messages_csv(
            user_id=user.id,
            channel_id=channel_id,
            channel_ids=channel_ids,
            start_date=start_date,
            end_date=end_date,
            media_types=media_types,
        ),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/html")
async def export_messages_html(
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(200, ge=1, le=5000),
    media_types: Optional[list[str]] = Query(None),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Export filtered messages to formatted HTML with audit logging.

    Generates a styled HTML document of messages matching the specified filters.
    Includes embedded media references and preserves message formatting. Limited to 5000 messages.
    """
    record_audit_event(
        db=db,
        user_id=user.id,
        action="message.export.html",
        resource_type="message",
        resource_id=str(channel_id) if channel_id else None,
        metadata={
            "format": "html",
            "channel_id": str(channel_id) if channel_id else None,
            "channel_ids": [str(cid) for cid in channel_ids] if channel_ids else None,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "limit": limit,
            "media_types": media_types,
        },
    )

    filename = "osfeed-messages.html"
    return StreamingResponse(
        service_export_messages_html(
            user_id=user.id,
            channel_id=channel_id,
            channel_ids=channel_ids,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            media_types=media_types,
        ),
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )




@router.get("/export/pdf")
async def export_messages_pdf(
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(200, ge=1, le=1000),
    media_types: Optional[list[str]] = Query(None),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Export filtered messages to professional PDF format with audit logging.

    Generates a formatted PDF document of messages matching the specified filters.
    Suitable for archiving and sharing. Limited to 1000 messages per export.
    """
    record_audit_event(
        db=db,
        user_id=user.id,
        action="message.export.pdf",
        resource_type="message",
        resource_id=str(channel_id) if channel_id else None,
        metadata={
            "format": "pdf",
            "channel_id": str(channel_id) if channel_id else None,
            "channel_ids": [str(cid) for cid in channel_ids] if channel_ids else None,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "limit": limit,
            "media_types": media_types,
        },
    )

    pdf_bytes = await service_export_messages_pdf(
        user_id=user.id,
        channel_id=channel_id,
        channel_ids=channel_ids,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        media_types=media_types,
    )

    filename = "osfeed-messages.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{message_id}/media")
async def get_message_media(
    message_id: UUID,
    user: User = Depends(current_active_user),
):
    """Stream message media directly from Telegram without server-side storage.

    Proxies media bytes from Telegram's servers directly to the client, avoiding
    local storage requirements. Includes 24-hour browser caching for performance.
    """
    media_bytes, content_type = await get_media_stream(message_id, user.id)

    return StreamingResponse(
        media_bytes,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": "inline",
        },
    )


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single message by its unique identifier with authorization check.

    Returns the complete message details including channel info, translations, and metadata.
    Verifies the user has access to the message's channel before returning data.
    """
    message = await get_single_message(message_id, user.id, db)

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return message_to_response(message)


@router.get("/{message_id}/similar", response_model=SimilarMessagesResponse)
@response_cache(expire=300, namespace="messages-similar")
async def get_similar_messages(
    message_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Find similar or duplicate messages grouped by duplicate_group_id.

    Returns all messages sharing the same duplicate_group_id as the specified message.
    Useful for identifying cross-posted content. Results are cached for 5 minutes.
    """
    messages, duplicate_group_id = await get_similar_messages_service(
        message_id=message_id,
        user_id=user.id,
        db=db,
    )

    # Service returns ([], None) if source message not found or has no duplicate_group_id
    # Check if source message exists by trying to fetch it
    if duplicate_group_id is None and not messages:
        result = await db.execute(
            select(Message).where(Message.id == message_id)
        )
        source_message = result.scalar_one_or_none()
        if not source_message:
            raise HTTPException(status_code=404, detail="Message not found")

    return SimilarMessagesResponse(
        messages=[message_to_response(message) for message in messages],
        total=len(messages),
        page=1,
        page_size=len(messages),
        duplicate_group_id=duplicate_group_id,
    )


@router.post("/{message_id}/translate", response_model=MessageResponse)
async def translate_message_on_demand(
    message_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Translate a single message on-demand to the user's preferred language with real-time updates.

    Triggers immediate translation of the specified message and publishes the result via
    Redis Pub/Sub for real-time client updates. Creates an audit trail of the translation request.
    """
    # Verify user has access to this message
    message = await get_single_message(message_id, user.id, db)

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Get target language from settings
    target_language = settings.preferred_language

    # Record audit event
    record_audit_event(
        db=db,
        user_id=user.id,
        action="message.translate.single",
        resource_type="message",
        resource_id=str(message_id),
        metadata={
            "target_language": target_language,
        },
    )

    try:
        # Use service to translate the message
        message = await translate_single_message(
            message_id=message_id,
            target_language=target_language,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Publish event for real-time updates across all clients
    if message.translated_text:
        await publish_message_translated(
            message_id=message.id,
            channel_id=message.channel_id,
            translated_text=message.translated_text,
            source_language=message.source_language or "",
            target_language=message.target_language or target_language,
        )

    return message_to_response(message)
