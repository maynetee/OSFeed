from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update
from uuid import UUID

from app.database import get_db, AsyncSessionLocal
from app.models.message import Message
from app.models.channel import Channel
from app.models.user import User
from app.schemas.message import MessageResponse, MessageListResponse
from app.services.translator import translator
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


@router.get("", response_model=MessageListResponse)
async def list_messages(
    channel_id: Optional[UUID] = None,
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

    if channel_id:
        query = query.where(Message.channel_id == channel_id)

    if start_date:
        query = query.where(Message.published_at >= start_date)

    if end_date:
        query = query.where(Message.published_at <= end_date)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

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
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Message, Channel).join(Channel)
    if channel_id:
        query = query.where(Message.channel_id == channel_id)
    if start_date:
        query = query.where(Message.published_at >= start_date)
    if end_date:
        query = query.where(Message.published_at <= end_date)

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
