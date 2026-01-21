"""
Real-time Telegram message collector using Telethon event handlers.

This service listens for new messages from followed channels in real-time,
rather than polling every few minutes. Includes auto-reconnect on errors.
"""
from telethon import TelegramClient, events
from telethon.tl.types import Channel
from telethon.errors import FloodWaitError, ConnectionError as TelethonConnectionError
from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.channel import Channel as ChannelModel
from app.models.message import Message
from app.services.telegram_collector import _connect_lock
from app.services.translator import translator
from app.services.translation_pool import run_translation
from sqlalchemy import select, update
from datetime import datetime, timezone
import asyncio
import os
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Reconnection settings
RECONNECT_BASE_DELAY = 5  # seconds
RECONNECT_MAX_DELAY = 300  # 5 minutes


class RealtimeCollector:
    """Real-time Telegram message collector with auto-reconnect.

    This collector listens for new messages in real-time using Telethon's
    event handlers. It automatically reconnects on connection errors and
    handles FloodWaitErrors gracefully.
    """

    def __init__(self):
        self.api_id = settings.telegram_api_id
        self.api_hash = settings.telegram_api_hash
        self.phone = settings.telegram_phone
        self.client = None
        self.running = False
        self._channel_ids = set()  # Telegram channel IDs we're monitoring
        self._reconnect_attempts = 0
        self._tasks: set[asyncio.Task] = set()  # Track running tasks
        self._flood_wait_seconds: int = 0  # FloodWait delay from handlers
        self._flood_wait_lock = asyncio.Lock()  # Protect flood wait state

    async def start(self):
        """Start the real-time collector with auto-reconnect loop."""
        if self.running:
            return

        self.running = True
        logger.info("Starting real-time collector...")

        # Start the main loop with auto-reconnect, tracking the task
        task = asyncio.create_task(self._run_with_reconnect())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _run_with_reconnect(self):
        """Main loop that handles reconnection on errors."""
        while self.running:
            try:
                await self._connect_and_listen()
            except FloodWaitError as e:
                wait_time = e.seconds
                logger.warning(
                    f"FloodWaitError in real-time collector: waiting {wait_time}s"
                )
                await self._handle_flood_wait(wait_time)
            except (ConnectionError, TelethonConnectionError, OSError) as e:
                delay = min(
                    RECONNECT_BASE_DELAY * (2 ** self._reconnect_attempts),
                    RECONNECT_MAX_DELAY
                )
                self._reconnect_attempts += 1
                logger.warning(
                    f"Connection error in real-time collector: {e}. "
                    f"Reconnecting in {delay}s (attempt {self._reconnect_attempts})"
                )
                await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Unexpected error in real-time collector: {e}")
                await asyncio.sleep(30)  # Wait before retrying

        logger.info("Real-time collector stopped")

    async def _handle_flood_wait(self, wait_seconds: int):
        """Handle FloodWaitError with controlled wait and reconnect.

        Args:
            wait_seconds: Number of seconds to wait before reconnecting.
        """
        async with self._flood_wait_lock:
            # Use the maximum wait time if multiple flood waits occur
            effective_wait = max(self._flood_wait_seconds, wait_seconds)
            self._flood_wait_seconds = 0  # Reset for next cycle

        logger.info(f"FloodWait: sleeping for {effective_wait}s before reconnect")
        await asyncio.sleep(effective_wait)
        self._reconnect_attempts = 0  # Reset after successful wait

    async def _connect_and_listen(self):
        """Connect to Telegram and start listening for messages."""
        os.makedirs("data", exist_ok=True)

        # Use the same session file as the regular collector
        async with _connect_lock:
            self.client = TelegramClient(
                "data/telegram_session",
                self.api_id,
                self.api_hash
            )
            await self.client.start(phone=self.phone)

        self._reconnect_attempts = 0  # Reset on successful connection
        logger.info("Real-time collector connected to Telegram")

        # Load channels we're following
        await self.refresh_channels()

        # Register event handler for new messages
        @self.client.on(events.NewMessage())
        async def handle_new_message(event):
            await self._process_message(event)

        logger.info("Real-time collector listening for messages")

        # Keep the client running and periodically refresh channels
        await self._keep_alive()

    async def _keep_alive(self):
        """Keep the client connection alive and refresh channel list."""
        while self.running and self.client and self.client.is_connected():
            await asyncio.sleep(60)
            # Periodically refresh channel list
            try:
                await self.refresh_channels()
            except Exception as e:
                logger.warning(f"Error refreshing channels: {e}")

    async def refresh_channels(self):
        """Refresh the list of channels we're monitoring."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ChannelModel.telegram_id).where(
                    ChannelModel.is_active == True,
                    ChannelModel.telegram_id.isnot(None),
                )
            )
            channel_ids = {row[0] for row in result.all()}
            self._channel_ids = channel_ids
            logger.debug(f"Monitoring {len(channel_ids)} channels")

    async def _process_message(self, event):
        """Process an incoming message with error handling."""
        try:
            # Check if message is from a channel we're following
            if not event.is_channel:
                return

            chat = await event.get_chat()
            if not isinstance(chat, Channel):
                return

            telegram_id = chat.id
            if telegram_id not in self._channel_ids:
                return

            # Skip messages without text
            if not event.message.text:
                return

            logger.info(f"New real-time message from {chat.title}")

            # Get channel from database
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(ChannelModel).where(ChannelModel.telegram_id == telegram_id)
                )
                channel = result.scalar_one_or_none()

                if not channel:
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

                channel_id = channel.id

            # Determine media type
            media_type = None
            media_urls = []
            if event.message.media:
                if hasattr(event.message.media, 'photo'):
                    media_type = 'photo'
                elif hasattr(event.message.media, 'document'):
                    media_type = 'document'
                elif hasattr(event.message.media, 'video'):
                    media_type = 'video'

            # Save to database
            message_id = None
            async with AsyncSessionLocal() as db:
                message = Message(
                    channel_id=channel_id,
                    telegram_message_id=event.message.id,
                    original_text=event.message.text,
                    translated_text=None,
                    source_language=None,
                    target_language=settings.preferred_language,
                    needs_translation=True,
                    media_type=media_type,
                    media_urls=media_urls,
                    published_at=event.message.date,
                    translated_at=None,
                )
                db.add(message)
                await db.commit()
                # Refresh to get ID
                await db.refresh(message)
                message_id = message.id

            logger.info(
                f"Saved real-time message from {chat.title}: "
                f"{event.message.text[:50]}..."
            )
            
            # Trigger instant translation in background
            if message_id and event.message.text:
                 asyncio.create_task(self._translate_new_message(
                     message_id, 
                     event.message.text, 
                     event.message.date
                 ))

        except FloodWaitError as e:
            # Signal the reconnect loop to handle FloodWait gracefully
            # instead of raising, which could disrupt the event handler
            logger.warning(
                f"FloodWaitError processing message: {e.seconds}s wait required. "
                "Signaling reconnect loop."
            )
            async with self._flood_wait_lock:
                self._flood_wait_seconds = max(self._flood_wait_seconds, e.seconds)
            # Don't re-raise - let the _keep_alive loop detect the disconnection
            # or wait for the flood wait period naturally
        except Exception as e:
            logger.error(f"Error processing real-time message: {e}")

    async def _translate_new_message(self, message_id, text, published_at):
        """Translate a newly arrived message immediately."""
        try:
            target_lang = settings.preferred_language
            
            # Run translation (using shared pool to respect concurrency limits)
            translated_text, source_lang, priority = await run_translation(
                translator.translate(
                    text,
                    target_lang=target_lang,
                    published_at=published_at
                )
            )
            
            if priority == "skip":
                need_update = True
                translated_text = None
            else:
                need_update = True

            if need_update:
                async with AsyncSessionLocal() as db:
                    await db.execute(
                        update(Message)
                        .where(Message.id == message_id)
                        .values(
                            translated_text=translated_text,
                            source_language=source_lang,
                            target_language=target_lang,
                            needs_translation=False,
                            translated_at=datetime.now(timezone.utc),
                            translation_priority=priority,
                        )
                    )
                    await db.commit()
                logger.info(f"Instantly translated message {message_id} ({source_lang}->{target_lang})")
                
        except Exception as e:
            logger.error(f"Failed to instant-translate message {message_id}: {e}")

    async def stop(self):
        """Stop the real-time collector and cleanup all tasks."""
        logger.info("Stopping real-time collector...")
        self.running = False

        # Cancel and await all tracked tasks
        if self._tasks:
            logger.debug(f"Cancelling {len(self._tasks)} tracked tasks")
            for task in self._tasks:
                if not task.done():
                    task.cancel()

            # Wait for all tasks to complete (with cancellation)
            results = await asyncio.gather(*self._tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception) and not isinstance(
                    result, asyncio.CancelledError
                ):
                    logger.warning(f"Task {i} ended with error: {result}")
            self._tasks.clear()

        if self.client:
            try:
                await self.client.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting client: {e}")
            self.client = None
        logger.info("Real-time collector stopped")


# Singleton instance
realtime_collector = RealtimeCollector()
