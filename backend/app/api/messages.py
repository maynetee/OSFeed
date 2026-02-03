from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update, or_, tuple_, insert, and_, literal
from sqlalchemy.orm import selectinload
from uuid import UUID
import asyncio
import json

from app.database import get_db, AsyncSessionLocal
from app.models.message import Message, MessageTranslation
from app.utils.response_cache import response_cache
from app.utils.export import generate_html_template, generate_html_article, generate_pdf_bytes
from app.models.channel import Channel
from app.models.user import User
from app.schemas.message import MessageResponse, MessageListResponse, SimilarMessagesResponse
from app.services.translation_pool import run_translation
from app.services.translator import translator
from app.services.message_utils import message_to_response, apply_message_filters
from app.services.message_streaming_service import create_message_stream
from app.services.message_export_service import (
    export_messages_csv as service_export_messages_csv,
    export_messages_html as service_export_messages_html,
)
from app.config import get_settings
from app.services.fetch_queue import enqueue_fetch_job
from app.auth.users import current_active_user
from app.services.cache import get_redis_client
from app.services.events import publish_message_translated
from app.services.audit import record_audit_event
from datetime import datetime, timezone
from typing import Optional
import base64
import logging
from io import BytesIO

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
    except Exception as exc:
        logger.warning(f"Failed to decode cursor: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=400, detail="Invalid cursor format")


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
    """Get paginated message feed with optional filters."""
    query = select(Message).options(selectinload(Message.channel))
    query = apply_message_filters(query, user.id, channel_id, channel_ids, start_date, end_date, media_types)

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
    offset: int = Query(0, ge=0),
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
            func.coalesce(Message.translated_text, literal("")).ilike(search_term),
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
    except Exception as e:
        logger.error(f"Error searching messages for user {user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed")


@router.post("/fetch-historical/{channel_id}")
async def fetch_historical_messages(
    channel_id: UUID,
    days: int = Query(7, ge=0, le=3650),
    user: User = Depends(current_active_user),
):
    """Fetch historical messages for a channel."""
    async with AsyncSessionLocal() as db:
        from app.models.channel import user_channels
        result = await db.execute(
            select(Channel).join(
                user_channels, 
                and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user.id)
            ).where(Channel.id == channel_id)
        )
        channel = result.scalar_one_or_none()

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
    from app.models.channel import user_channels

    async with AsyncSessionLocal() as db_local:
        query = select(Message.id, Message.original_text, Message.published_at).where(
            Message.needs_translation.is_(True)
        )
        query = query.join(Channel, Message.channel_id == Channel.id).join(
            user_channels,
            and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user.id)
        )

        if channel_id:
            query = query.where(Message.channel_id == channel_id)

        result = await db_local.execute(query)
        messages_to_translate = [
            {'id': row.id, 'original_text': row.original_text, 'published_at': row.published_at}
            for row in result.all()
            if row.original_text
        ]

    if not messages_to_translate:
        return {"message": "No messages to translate"}

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
            "message_count": len(messages_to_translate),
        },
    )

    translated_count = 0
    start_time = datetime.now()
    
    message_ids = [m['id'] for m in messages_to_translate]
    cache_hits = {}

    async with AsyncSessionLocal() as db_local:
        cache_query = select(MessageTranslation).where(
            MessageTranslation.message_id.in_(message_ids),
            MessageTranslation.target_lang == target_language
        )
        cache_result = await db_local.execute(cache_query)
        for row in cache_result.scalars().all():
            cache_hits[row.message_id] = row
            
    to_batch_process = []
    messages_with_cache = []
    
    for msg in messages_to_translate:
        if msg['id'] in cache_hits:
            messages_with_cache.append((msg, cache_hits[msg['id']]))
        else:
            to_batch_process.append(msg)

    updates = []
    if messages_with_cache:
        for msg, cached in messages_with_cache:
            updates.append({
                'id': msg['id'],
                'translated_text': cached.translated_text,
                'source_language': 'detected-cache',
                'target_language': target_language,
                'needs_translation': False,
                'translated_at': datetime.now(timezone.utc),
                'translation_priority': 'cached',
            })
            translated_count += 1

    if to_batch_process:
        texts = [m['original_text'] for m in to_batch_process]
        published_dates = [m['published_at'] for m in to_batch_process]
        
        batch_results = await run_translation(
            translator.translate_batch(
                texts,
                target_lang=target_language,
                published_at_list=published_dates,
            )
        )
        
        new_translations = []
        
        for msg, (trans_text, source_lang, priority) in zip(to_batch_process, batch_results):
            updates.append({
                'id': msg['id'],
                'translated_text': trans_text,
                'source_language': source_lang,
                'target_language': target_language,
                'needs_translation': False,
                'translated_at': datetime.now(timezone.utc),
                'translation_priority': priority,
            })
            
            if trans_text:
                new_translations.append({
                    'message_id': msg['id'],
                    'target_lang': target_language,
                    'translated_text': trans_text,
                    'translated_by': user.id,
                })
            
            translated_count += 1

        if new_translations:
            async with AsyncSessionLocal() as db_local:
                from sqlalchemy.dialects.postgresql import insert as pg_insert
                stmt = pg_insert(MessageTranslation).values(new_translations)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=['message_id', 'target_lang']
                )
                await db_local.execute(stmt)
                await db_local.commit()

    if updates:
        async with AsyncSessionLocal() as db_local:
            chunk_size = 100
            for i in range(0, len(updates), chunk_size):
                chunk = updates[i:i + chunk_size]
                await db_local.execute(
                    update(Message),
                    chunk
                )
            await db_local.commit()

    duration = datetime.now() - start_time
    return {
        "message": f"Processed {translated_count} messages (Cache hits: {len(messages_with_cache)})",
        "duration_seconds": duration.total_seconds()
    }


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

    async with AsyncSessionLocal() as db_local:
        query = select(Message, Channel)
        query = apply_message_filters(query, user.id, channel_id, channel_ids, start_date, end_date, media_types)
        query = query.order_by(desc(Message.published_at))
        query = query.limit(limit)
        result = await db_local.execute(query)
        rows = result.all()

    if not rows:
        return StreamingResponse(
            BytesIO(b""),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=osfeed-messages.pdf"},
        )

    # Build HTML using shared utilities
    html_parts = [generate_html_template("OSFeed - Messages")]
    html_parts.append("<h1>OSFeed - Messages</h1>")

    for message, channel in rows:
        html_parts.append(generate_html_article(message, channel))

    html_parts.append("</body></html>")
    html_content = "".join(html_parts)

    # Convert HTML to PDF using shared utility
    pdf_bytes = await asyncio.to_thread(generate_pdf_bytes, html_content)

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
    from app.models.channel import user_channels

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Message)
            .options(selectinload(Message.channel))
            .join(Channel, Message.channel_id == Channel.id)
            .join(
                user_channels,
                and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user.id),
            )
            .where(Message.id == message_id)
        )
        message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if not message.media_type or message.media_type not in ("photo", "video"):
        raise HTTPException(status_code=404, detail="No media available for this message")

    channel_username = message.channel.username if message.channel else None
    if not channel_username:
        raise HTTPException(status_code=404, detail="Channel username not available")

    telegram_message_id = message.telegram_message_id

    try:
        from app.services.telegram_client import get_telegram_client

        telegram = get_telegram_client()
        client = await telegram.get_client()

        # Get the specific Telegram message to access its media
        tg_messages = await client.get_messages(channel_username, ids=[telegram_message_id])
        if not tg_messages or not tg_messages[0]:
            raise HTTPException(status_code=404, detail="Telegram message not found")

        tg_msg = tg_messages[0]
        if not tg_msg.media:
            raise HTTPException(status_code=404, detail="No media in Telegram message")

        # Download media to memory
        media_bytes = BytesIO()
        await client.download_media(tg_msg, file=media_bytes)
        media_bytes.seek(0)

        # Determine content type
        if message.media_type == "photo":
            content_type = "image/jpeg"
        elif message.media_type == "video":
            content_type = "video/mp4"
        else:
            content_type = "application/octet-stream"

        return StreamingResponse(
            media_bytes,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=86400",
                "Content-Disposition": "inline",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch media for message {message_id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch media from Telegram")


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single message by ID."""
    result = await db.execute(
        select(Message)
        .options(selectinload(Message.channel))
        .join(Channel, Message.channel_id == Channel.id)
        .join(
            user_channels,
            and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user.id),
        )
        .where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()

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
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    source_message = result.scalar_one_or_none()

    if not source_message:
        raise HTTPException(status_code=404, detail="Message not found")

    if not source_message.duplicate_group_id:
        return SimilarMessagesResponse(
            messages=[],
            total=0,
            page=1,
            page_size=0,
            duplicate_group_id=None,
        )

    query = (
        select(Message)
        .options(selectinload(Message.channel))
        .join(Channel, Message.channel_id == Channel.id)
        .join(
            user_channels,
            and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user.id)
        )
        .where(
            and_(
                Message.duplicate_group_id == source_message.duplicate_group_id,
                Message.id != message_id
            )
        )
        .order_by(desc(Message.published_at), desc(Message.id))
    )

    result = await db.execute(query)
    messages = result.scalars().all()

    return SimilarMessagesResponse(
        messages=[message_to_response(message) for message in messages],
        total=len(messages),
        page=1,
        page_size=len(messages),
        duplicate_group_id=source_message.duplicate_group_id,
    )


@router.post("/{message_id}/translate", response_model=MessageResponse)
async def translate_message_on_demand(
    message_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Translate a message on demand."""
    async with AsyncSessionLocal() as db_local:
        result = await db_local.execute(
            select(Message).options(selectinload(Message.channel)).where(Message.id == message_id)
        )
        message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Record audit event
    target_language = message.target_language or settings.preferred_language
    record_audit_event(
        db=db,
        user_id=user.id,
        action="message.translate.single",
        resource_type="message",
        resource_id=str(message_id),
        metadata={
            "target_language": target_language,
            "channel_id": str(message.channel_id) if message.channel_id else None,
        },
    )

    if not message.needs_translation:
        return message_to_response(message)

    original_text = message.original_text or ""
    if not original_text.strip():
        async with AsyncSessionLocal() as db_local:
            await db_local.execute(
                update(Message)
                .where(Message.id == message_id)
                .values(needs_translation=False, translation_priority="skip")
            )
            await db_local.commit()
        message.needs_translation = False
        return message_to_response(message)
    translated_text, source_lang, priority = await run_translation(
        translator.translate(
            original_text,
            source_lang=message.source_language,
            target_lang=target_language,
            published_at=message.published_at,
        )
    )

    async with AsyncSessionLocal() as db_local:
        await db_local.execute(
            update(Message)
            .where(Message.id == message_id)
            .values(
                translated_text=translated_text,
                source_language=source_lang,
                target_language=target_language,
                needs_translation=False,
                translated_at=datetime.now(timezone.utc),
                translation_priority=priority,
            )
        )
        await db_local.commit()
        refreshed = await db_local.execute(
            select(Message).options(selectinload(Message.channel)).where(Message.id == message_id)
        )
        message = refreshed.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Publish event for real-time updates across all clients
    await publish_message_translated(
        message_id=message.id,
        channel_id=message.channel_id,
        translated_text=translated_text,
        source_language=source_lang,
        target_language=target_language
    )

    return message_to_response(message)
