"""Message Media Service

This module provides functions for proxying media from Telegram without storing it on the server.
"""

import logging
from io import BytesIO
from typing import Tuple
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from telethon.errors import RPCError

from app.database import AsyncSessionLocal
from app.models.message import Message
from app.models.channel import Channel, user_channels

logger = logging.getLogger(__name__)


async def get_media_stream(message_id: UUID, user_id: UUID) -> Tuple[BytesIO, str]:
    """Get media stream for a message from Telegram.

    Streams the media bytes directly from Telegram to the client without storing
    it on the server. Validates user access to the message's channel before
    proxying the media.

    Args:
        message_id: UUID of the message to get media for
        user_id: UUID of the user requesting the media

    Returns:
        Tuple of (media_bytes, content_type) where:
            - media_bytes: BytesIO containing the media data
            - content_type: MIME type string for the media

    Raises:
        HTTPException: If message not found, user lacks access, no media available,
                      or Telegram fetch fails
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Message)
            .options(selectinload(Message.channel))
            .join(Channel, Message.channel_id == Channel.id)
            .join(
                user_channels,
                and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user_id),
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

        return media_bytes, content_type

    except HTTPException:
        raise
    except RPCError as e:
        logger.exception(f"Failed to fetch media for message {message_id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch media from Telegram")
