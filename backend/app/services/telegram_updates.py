"""Telegram Real-time Update Handler.

Listens for new messages in subscribed channels and dispatches them
to the message processor for immediate handling and SSE broadcast.
"""
import asyncio
import logging
from typing import Set, Optional
from datetime import datetime, timezone

from telethon import events
from telethon.tl.types import Channel as TelegramChannel

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.channel import Channel
from app.models.message import Message
from app.services.telegram_client import get_telegram_client
from sqlalchemy import select

logger = logging.getLogger(__name__)


class TelegramUpdateHandler:
    """Handles real-time message updates from Telegram.

    Subscribes to channels and processes new messages as they arrive,
    storing them in the database and publishing to Redis for SSE.
    """

    def __init__(self):
        self._subscribed_channels: Set[str] = set()
        self._running = False
        self._handler_registered = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start listening for real-time updates."""
        if self._running:
            logger.warning("Update handler already running")
            return

        self._running = True
        logger.info("Starting Telegram update handler")

        try:
            telegram_manager = get_telegram_client()
            client = await telegram_manager.get_client()

            # Register the new message handler
            if not self._handler_registered:
                @client.on(events.NewMessage())
                async def handler(event):
                    await self._on_new_message(event)

                self._handler_registered = True
                logger.info("Registered new message event handler")

            # Subscribe to all active channels
            await self._subscribe_all_active_channels()

            logger.info("Telegram update handler started")

        except Exception as e:
            logger.exception(f"Failed to start update handler: {e}")
            self._running = False
            raise

    async def stop(self) -> None:
        """Stop the update handler gracefully."""
        if not self._running:
            return

        logger.info("Stopping Telegram update handler")
        self._running = False
        self._subscribed_channels.clear()

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("Telegram update handler stopped")

    async def subscribe_channel(self, channel: Channel) -> None:
        """Add a channel to the subscription list.

        Args:
            channel: Channel model instance
        """
        username = channel.username.lower()

        if username in self._subscribed_channels:
            return

        self._subscribed_channels.add(username)
        logger.info(f"Subscribed to real-time updates for @{channel.username}")

    async def unsubscribe_channel(self, username: str) -> None:
        """Remove a channel from subscriptions.

        Args:
            username: Channel username
        """
        username = username.lower().lstrip("@")
        self._subscribed_channels.discard(username)
        logger.info(f"Unsubscribed from @{username}")

    async def _subscribe_all_active_channels(self) -> None:
        """Subscribe to all active channels in the database."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Channel).where(Channel.is_active == True)
            )
            channels = result.scalars().all()

        for channel in channels:
            await self.subscribe_channel(channel)

        logger.info(f"Subscribed to {len(self._subscribed_channels)} channels")

    async def _on_new_message(self, event) -> None:
        """Handle an incoming new message event.

        Args:
            event: Telethon NewMessage event
        """
        if not self._running:
            return

        try:
            # Check if this is from a subscribed channel
            chat = await event.get_chat()

            if not isinstance(chat, TelegramChannel):
                return

            username = (chat.username or "").lower()
            if not username or username not in self._subscribed_channels:
                return

            # Find the channel in our database
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Channel).where(Channel.username.ilike(username))
                )
                channel = result.scalar_one_or_none()

                if not channel:
                    logger.debug(f"Received message for unknown channel: {username}")
                    return

                # Check if message already exists
                existing = await db.execute(
                    select(Message).where(
                        Message.channel_id == channel.id,
                        Message.telegram_message_id == event.message.id
                    )
                )
                if existing.scalar_one_or_none():
                    return

                # Create new message
                msg = await self._process_message(event.message, channel)
                db.add(msg)
                await db.commit()
                await db.refresh(msg)

                logger.info(
                    f"Real-time message received: {channel.username} - "
                    f"msg_id={event.message.id}"
                )

                # Publish to Redis for SSE
                await self._publish_new_message(msg)

        except Exception as e:
            logger.exception(f"Error handling new message: {e}")

    async def _process_message(self, tg_msg, channel: Channel) -> Message:
        """Convert Telethon message to Message model.

        Args:
            tg_msg: Telethon message object
            channel: Channel model instance

        Returns:
            Message model instance
        """
        # Determine media type
        media_type = None
        if tg_msg.photo:
            media_type = "photo"
        elif tg_msg.video:
            media_type = "video"
        elif tg_msg.document:
            media_type = "document"
        elif tg_msg.audio:
            media_type = "audio"

        text = tg_msg.text or tg_msg.message or ""

        published_at = datetime.now(timezone.utc)
        if tg_msg.date:
            published_at = tg_msg.date.replace(tzinfo=timezone.utc)

        return Message(
            channel_id=channel.id,
            telegram_message_id=tg_msg.id,
            original_text=text,
            media_type=media_type,
            media_urls=[],
            published_at=published_at,
            fetched_at=datetime.now(timezone.utc),
            needs_translation=bool(text.strip()),
            is_duplicate=False,
            originality_score=100
        )

    async def _publish_new_message(self, message: Message) -> None:
        """Publish new message event to Redis for SSE broadcast.

        Args:
            message: Message model instance
        """
        try:
            from redis.asyncio import Redis
            import json

            if not settings.redis_url:
                return

            redis = Redis.from_url(settings.redis_url, decode_responses=True)

            event_data = {
                "type": "message:new",
                "data": {
                    "message_id": str(message.id),
                    "channel_id": str(message.channel_id),
                    "published_at": message.published_at.isoformat()
                }
            }

            await redis.publish("osfeed:events", json.dumps(event_data))
            await redis.close()

            logger.debug(f"Published message:new event for {message.id}")

        except Exception as e:
            logger.error(f"Failed to publish message event: {e}")


# Singleton instance
_update_handler: Optional[TelegramUpdateHandler] = None


def get_update_handler() -> TelegramUpdateHandler:
    """Get the singleton update handler instance."""
    global _update_handler
    if _update_handler is None:
        _update_handler = TelegramUpdateHandler()
    return _update_handler


async def start_update_handler() -> None:
    """Start the update handler."""
    handler = get_update_handler()
    await handler.start()


async def stop_update_handler() -> None:
    """Stop the update handler."""
    global _update_handler
    if _update_handler:
        await _update_handler.stop()
        _update_handler = None
