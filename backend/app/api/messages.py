from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update, or_
from uuid import UUID

from app.database import get_db, AsyncSessionLocal
from app.models.message import Message
from app.models.channel import Channel
from app.models.user import User
from app.schemas.message import MessageResponse, MessageListResponse
from app.services.translator import translator
from app.services.vector_store import vector_store
from app.config import get_settings
from app.services.telegram_collector import TelegramCollector
from app.auth.users import current_active_user
from datetime import datetime, timezone
from typing import Optional
import json
import csv
from io import StringIO

router = APIRouter()
settings = get_settings()


def _apply_message_filters(
    query,
    channel_id: Optional[UUID],
    channel_ids: Optional[list[UUID]],
    start_date: Optional[datetime],
    end_date: Optional[datetime],
):
    if channel_ids:
        query = query.where(Message.channel_id.in_(channel_ids))
    elif channel_id:
        query = query.where(Message.channel_id == channel_id)

    if start_date:
        query = query.where(Message.published_at >= start_date)

    if end_date:
        query = query.where(Message.published_at <= end_date)

    return query


@router.get("", response_model=MessageListResponse)
async def list_messages(
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated message feed with optional filters.

    Requires authentication.
    """
    # Build query
    query = select(Message)

    query = _apply_message_filters(query, channel_id, channel_ids, start_date, end_date)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated messages
    query = query.order_by(desc(Message.published_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    messages = result.scalars().all()

    return MessageListResponse(
        messages=messages,
        total=total,
        page=offset // limit + 1,
        page_size=limit
    )


@router.get("/search", response_model=MessageListResponse)
async def search_messages(
    q: str = Query(..., min_length=3),
    channel_ids: Optional[list[UUID]] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Search messages via full-text match on original/translated text."""
    query = select(Message).where(
        or_(
            Message.original_text.ilike(f"%{q}%"),
            Message.translated_text.ilike(f"%{q}%"),
        )
    )
    query = _apply_message_filters(query, None, channel_ids, start_date, end_date)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(desc(Message.published_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    messages = result.scalars().all()

    return MessageListResponse(
        messages=messages,
        total=total,
        page=offset // limit + 1,
        page_size=limit,
    )


@router.get("/search/semantic", response_model=MessageListResponse)
async def search_messages_semantic(
    q: str = Query(..., min_length=3),
    channel_ids: Optional[list[UUID]] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    top_k: int = Query(20, ge=1, le=100),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Search messages using semantic similarity."""
    if not vector_store.is_ready:
        return MessageListResponse(messages=[], total=0, page=1, page_size=top_k)

    raw_filter: dict = {}
    if channel_ids:
        raw_filter["channel_id"] = {"$in": [str(channel_id) for channel_id in channel_ids]}

    if start_date or end_date:
        ts_filter: dict = {}
        if start_date:
            ts_filter["$gte"] = int(start_date.timestamp())
        if end_date:
            ts_filter["$lte"] = int(end_date.timestamp())
        raw_filter["published_at_ts"] = ts_filter

    matches = vector_store.query_similar(text=q, top_k=top_k, filter=raw_filter or None)
    if not matches:
        return MessageListResponse(messages=[], total=0, page=1, page_size=top_k)

    ordered_ids = [match["id"] for match in matches]
    result = await db.execute(select(Message).where(Message.id.in_(ordered_ids)))
    messages = result.scalars().all()
    message_map = {str(message.id): message for message in messages}

    ordered_messages = []
    for match in matches:
        message = message_map.get(str(match["id"]))
        if not message:
            continue
        message.similarity_score = match.get("score")
        ordered_messages.append(message)

    return MessageListResponse(
        messages=ordered_messages,
        total=len(ordered_messages),
        page=1,
        page_size=top_k,
    )


@router.post("/fetch-historical/{channel_id}")
async def fetch_historical_messages(
    channel_id: UUID,
    days: int = Query(7, ge=1, le=30),
    user: User = Depends(current_active_user),
    background_tasks: BackgroundTasks = None,
):
    """Fetch historical messages for a channel (7 days by default).

    Requires authentication.
    """
    async with AsyncSessionLocal() as db:
        # Get channel
        result = await db.execute(select(Channel).where(Channel.id == channel_id))
        channel = result.scalar_one_or_none()

        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")

    # Fetch messages in background
    if background_tasks:
        background_tasks.add_task(fetch_and_store_messages, channel_id, channel.username, days)
        return {"message": f"Fetching messages from last {days} days in background"}
    else:
        await fetch_and_store_messages(channel_id, channel.username, days)
        return {"message": f"Fetched messages from last {days} days"}


async def fetch_and_store_messages(channel_id: UUID, username: str, days: int):
    """Background task to fetch and store historical messages.

    IMPORTANT: Releases DB lock during slow operations (Telegram fetch, translation).
    """
    collector = TelegramCollector()

    try:
        # Step 1: Fetch messages from Telegram (NO DB session)
        messages = await collector.get_messages_since(username, days=days, max_messages=500)

        if not messages:
            print(f"No messages found for channel {username}")
            return

        # Step 2: Get existing message IDs (short DB session)
        async with AsyncSessionLocal() as db:
            existing_result = await db.execute(
                select(Message.telegram_message_id).where(
                    Message.channel_id == channel_id,
                    Message.telegram_message_id.in_([m['message_id'] for m in messages])
                )
            )
            existing_ids = set(existing_result.scalars().all())

        # Filter to only new messages
        new_messages = [m for m in messages if m['message_id'] not in existing_ids]

        if not new_messages:
            print(f"No new messages for channel {username}")
            return

        # Step 3: Translate messages (NO DB session - this is slow)
        translated_messages = []
        for msg_data in new_messages:
            translated_text, source_lang = await translator.translate(msg_data['text'])
            translated_messages.append({
                'telegram_message_id': msg_data['message_id'],
                'original_text': msg_data['text'],
                'translated_text': translated_text,
                'source_language': source_lang,
                'target_language': settings.preferred_language,
                'media_type': msg_data.get('media_type'),
                'media_urls': json.dumps(msg_data.get('media_urls', [])),
                'published_at': msg_data['date'],
                'translated_at': datetime.now(timezone.utc),
            })

        # Step 4: Save to DB (short DB session)
        async with AsyncSessionLocal() as db:
            for msg in translated_messages:
                message = Message(
                    channel_id=channel_id,
                    telegram_message_id=msg['telegram_message_id'],
                    original_text=msg['original_text'],
                    translated_text=msg['translated_text'],
                    source_language=msg['source_language'],
                    target_language=msg['target_language'],
                    media_type=msg['media_type'],
                    media_urls=msg['media_urls'],
                    published_at=msg['published_at'],
                    translated_at=msg['translated_at'],
                )
                db.add(message)

            await db.commit()
            print(f"Stored {len(translated_messages)} historical messages for channel {username}")

    except Exception as e:
        print(f"Error fetching historical messages: {e}")
    finally:
        await collector.disconnect()


@router.post("/translate")
async def translate_messages(
    target_language: str = Query(..., description="Target language code (en, fr, es, etc.)"),
    channel_id: Optional[UUID] = None,
    user: User = Depends(current_active_user),
):
    """Re-translate messages to a new target language.

    Requires authentication.
    IMPORTANT: Releases DB lock during slow translation operations.
    """
    # Step 1: Load messages from DB (short session)
    async with AsyncSessionLocal() as db:
        query = select(Message.id, Message.original_text)
        if channel_id:
            query = query.where(Message.channel_id == channel_id)

        result = await db.execute(query)
        messages_to_translate = [
            {'id': row.id, 'original_text': row.original_text}
            for row in result.all()
            if row.original_text
        ]

    if not messages_to_translate:
        return {"message": "No messages to translate"}

    # Step 2: Translate messages (NO DB session - this is slow)
    translations = []
    for msg in messages_to_translate:
        translated_text, detected_lang = await translator.translate(
            msg['original_text'],
            source_lang=None,  # Force re-detection
            target_lang=target_language
        )
        translations.append({
            'id': msg['id'],
            'translated_text': translated_text,
            'source_language': detected_lang,
        })

    # Step 3: Save translations to DB (short session)
    async with AsyncSessionLocal() as db:
        for trans in translations:
            await db.execute(
                update(Message)
                .where(Message.id == trans['id'])
                .values(
                    translated_text=trans['translated_text'],
                    source_language=trans['source_language'],
                    target_language=target_language,
                    translated_at=datetime.now(timezone.utc),
                )
            )
        await db.commit()

    return {"message": f"Translated {len(translations)} messages to {target_language}"}


@router.get("/export/csv")
async def export_messages_csv(
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Message, Channel).join(Channel)
    query = _apply_message_filters(query, channel_id, channel_ids, start_date, end_date)

    result = await db.execute(query.order_by(desc(Message.published_at)))
    rows = result.all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "message_id",
        "channel_title",
        "channel_username",
        "published_at",
        "original_text",
        "translated_text",
        "source_language",
        "target_language",
        "is_duplicate",
    ])
    for message, channel in rows:
        writer.writerow([
            str(message.id),
            channel.title,
            channel.username,
            message.published_at,
            message.original_text or "",
            message.translated_text or "",
            message.source_language or "",
            message.target_language or "",
            message.is_duplicate,
        ])

    output.seek(0)
    filename = "telescope-messages.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/html")
async def export_messages_html(
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(200, ge=1, le=1000),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Message, Channel).join(Channel)
    query = _apply_message_filters(query, channel_id, channel_ids, start_date, end_date)
    result = await db.execute(query.order_by(desc(Message.published_at)).limit(limit))
    rows = result.all()

    from html import escape

    html_lines = [
        "<!DOCTYPE html>",
        "<html lang='fr'>",
        "<head><meta charset='utf-8'><title>TeleScope - Messages</title>",
        "<style>body{font-family:Arial,sans-serif;background:#f8fafc;color:#0f172a;padding:24px;}h1{font-size:20px;}article{margin:16px 0;padding:12px;border:1px solid #e2e8f0;border-radius:12px;background:#fff;}small{color:#64748b;}</style>",
        "</head><body>",
        "<h1>Export messages</h1>",
    ]

    for message, channel in rows:
        html_lines.append("<article>")
        html_lines.append(
            f"<small>{escape(channel.title)} · {escape(channel.username)} · {message.published_at}</small>"
        )
        html_lines.append(f"<p>{escape(message.translated_text or message.original_text or '')}</p>")
        if message.translated_text and message.original_text:
            html_lines.append(f"<p><small>Original: {escape(message.original_text)}</small></p>")
        html_lines.append("</article>")

    html_lines.append("</body></html>")
    html = "\n".join(html_lines)
    return StreamingResponse(
        iter([html]),
        media_type="text/html",
        headers={"Content-Disposition": "attachment; filename=telescope-messages.html"},
    )


@router.get("/export/pdf")
async def export_messages_pdf(
    channel_id: Optional[UUID] = None,
    channel_ids: Optional[list[UUID]] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(200, ge=1, le=500),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from io import BytesIO
    from fpdf import FPDF

    query = select(Message, Channel).join(Channel)
    query = _apply_message_filters(query, channel_id, channel_ids, start_date, end_date)
    result = await db.execute(query.order_by(desc(Message.published_at)).limit(limit))
    rows = result.all()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=14)
    pdf.cell(0, 10, "TeleScope - Messages", ln=True)
    pdf.set_font("Helvetica", size=11)
    for message, channel in rows:
        header = f"{channel.title} (@{channel.username}) - {message.published_at}"
        pdf.multi_cell(0, 8, header)
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(0, 6, message.translated_text or message.original_text or "")
        if message.translated_text and message.original_text:
            pdf.set_font("Helvetica", size=9)
            pdf.multi_cell(0, 6, f"Original: {message.original_text}")
        pdf.ln(2)
        pdf.set_font("Helvetica", size=11)

    output = pdf.output(dest="S")
    pdf_bytes = output.encode("latin-1", errors="ignore") if isinstance(output, str) else output
    filename = "telescope-messages.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single message by ID.

    Requires authentication.
    """
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return message


@router.get("/{message_id}/similar", response_model=MessageListResponse)
async def get_similar_messages(
    message_id: UUID,
    top_k: int = Query(5, ge=1, le=20),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get similar messages based on semantic vectors."""
    if not vector_store.is_ready:
        return MessageListResponse(messages=[], total=0, page=1, page_size=top_k)

    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    text = message.translated_text or message.original_text or ""
    if not text:
        return MessageListResponse(messages=[], total=0, page=1, page_size=top_k)

    matches = vector_store.query_similar(text=text, top_k=top_k + 1)
    matches = [match for match in matches if str(match.get("id")) != str(message_id)]

    ordered_ids = [match["id"] for match in matches]
    if not ordered_ids:
        return MessageListResponse(messages=[], total=0, page=1, page_size=top_k)

    result = await db.execute(select(Message).where(Message.id.in_(ordered_ids)))
    messages = result.scalars().all()
    message_map = {str(item.id): item for item in messages}

    ordered_messages = []
    for match in matches:
        similar_message = message_map.get(str(match["id"]))
        if not similar_message:
            continue
        similar_message.similarity_score = match.get("score")
        ordered_messages.append(similar_message)

    return MessageListResponse(
        messages=ordered_messages,
        total=len(ordered_messages),
        page=1,
        page_size=top_k,
    )
