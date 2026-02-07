import base64
import logging
from datetime import datetime, timezone
from io import BytesIO
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func, or_, select, tuple_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.users import current_active_user
from app.config import get_settings
from app.database import AsyncSessionLocal, get_db
from app.models.channel import Channel
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageListResponse, MessageResponse, SimilarMessagesResponse
from app.services.audit import record_audit_event
from app.services.channel_utils import get_authorized_channel
from app.services.events import publish_message_translated
from app.services.fetch_queue import enqueue_fetch_job
from app.services.message_export_service import (
    export_messages_csv as service_export_messages_csv,
)
from app.services.message_export_service import (
    export_messages_html as service_export_messages_html,
)
from app.services.message_export_service import (
    export_messages_pdf as service_export_messages_pdf,
)
from app.services.message_media_service import get_media_stream
from app.services.message_streaming_service import create_message_stream
from app.services.message_translation_bulk_service import translate_messages_batch, translate_single_message
from app.services.message_utils import (
    apply_message_filters,
    get_single_message,
    message_to_response,
)
from app.services.message_utils import (
    get_similar_messages as get_similar_messages_service,
)
from app.utils.response_cache import response_cache

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()


def _encode_cursor(published_at: datetime, message_id: UUID) -> str:
    cursor_value = f"{published_at.isoformat()}|{message_id}"
    return base64.urlsafe_b64encode(cursor_value.encode("utf-8")).decode("utf-8")


def _decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        published_at_raw, message_id_raw = decoded.split("|", 1)
        published_at = datetime.fromisoformat(published_at_raw)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        message_id = UUID(message_id_raw)
        return published_at, message_id
    except (ValueError, UnicodeDecodeError) as exc:
        logger.warning(f"Failed to decode cursor: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=400, detail="Invalid cursor format")


@router.get("", response_model=MessageListResponse)
@response_cache(expire=60, namespace="messages-list")
async def list_messages(
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=10000),
    cursor: Optional[str] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    media_types: Optional[list[str]] = Query(None),
    region: Optional[str] = Query(None, description="Filter by channel region"),
    topics: Optional[List[str]] = Query(None, description="Filter by channel topics"),
    sort: str = Query("latest", regex="^(latest|relevance)$"),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated message feed with optional filters."""
    # Pre-filter channel IDs by topics (cross-DB compatible: JSON handling differs between PG and SQLite)
    if topics:
        ch_result = await db.execute(select(Channel.id, Channel.topics).where(Channel.is_active.is_(True)))
        topic_filtered_ids = [
            ch_id for ch_id, ch_topics in ch_result.all()
            if ch_topics and any(t in ch_topics for t in topics)
        ]
        if not topic_filtered_ids:
            return MessageListResponse(messages=[], total=0, page=1, page_size=limit, next_cursor=None)
        if channel_ids:
            topic_filtered_ids = [cid for cid in topic_filtered_ids if cid in channel_ids]
            if not topic_filtered_ids:
                return MessageListResponse(messages=[], total=0, page=1, page_size=limit, next_cursor=None)
        channel_ids = topic_filtered_ids
        channel_id = None

    query = select(Message).options(selectinload(Message.channel))
    query = apply_message_filters(query, user.id, channel_id, channel_ids, start_date, end_date, media_types, region=region)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    if sort == "relevance":
        query = query.order_by(desc(Message.relevance_score).nullslast(), desc(Message.published_at), desc(Message.id))
        query = query.offset(offset)
    else:
        query = query.order_by(desc(Message.published_at), desc(Message.id))
        if cursor:
            cursor_published_at, cursor_id = _decode_cursor(cursor)
            query = query.where(tuple_(Message.published_at, Message.id) < (cursor_published_at, cursor_id))
        else:
            query = query.offset(offset)

    query = query.limit(limit)
    result = await db.execute(query)
    messages = result.scalars().all()

    next_cursor = None
    if sort != "relevance" and messages:
        last_message = messages[-1]
        next_cursor = _encode_cursor(last_message.published_at, last_message.id)

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
    """Stream messages via SSE. Uses Redis Pub/Sub for realtime updates."""
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
    offset: int = Query(0, ge=0, le=10000),
    cursor: Optional[str] = Query(None),
    media_types: Optional[list[str]] = Query(None),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Search messages via full-text match on original/translated text."""
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
            cursor_published_at, cursor_id = _decode_cursor(cursor)
            query = query.where(tuple_(Message.published_at, Message.id) < (cursor_published_at, cursor_id))
        else:
            query = query.offset(offset)
        query = query.limit(limit)
        result = await db.execute(query)
        messages = result.scalars().all()

        next_cursor = None
        if messages:
            last_message = messages[-1]
            next_cursor = _encode_cursor(last_message.published_at, last_message.id)

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
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        logger.error(f"Unexpected error searching messages for user {user.id}: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="MESSAGE_SEARCH_ERROR")
    except Exception as e:
        logger.error(f"Unhandled error searching messages for user {user.id}: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="MESSAGE_SEARCH_ERROR")


@router.post("/fetch-historical/{channel_id}")
async def fetch_historical_messages(
    channel_id: UUID,
    days: int = Query(7, ge=0, le=3650),
    user: User = Depends(current_active_user),
):
    """Fetch historical messages for a channel."""
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
    """Re-translate messages to a new target language."""
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
    """Export filtered messages to CSV format."""
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
    """Export filtered messages to HTML format."""
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
    """Export filtered messages to PDF format."""
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
    """Proxy media from Telegram without storing it on the server.

    Streams the media bytes directly from Telegram to the client.
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
    """Get a single message by ID."""
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
    """Get similar messages based on duplicate_group_id."""
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
    """Translate a message on demand."""
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
