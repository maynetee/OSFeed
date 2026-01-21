"""Telegram message collector with Flood Wait handling.

This module provides a collector class for fetching messages and channel info
from Telegram channels, with built-in rate limiting and exponential backoff
for handling FloodWaitErrors.
"""
from collections import OrderedDict
from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import FloodWaitError, SlowModeWaitError
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import asyncio
import logging

from app.config import get_settings
from app.utils.retry import telegram_retry

logger = logging.getLogger(__name__)
settings = get_settings()

# Lock only for connection initialization (SQLite session file)
_connect_lock = asyncio.Lock()

# Semaphore to limit concurrent Telegram operations (prevents FloodWait)
# This replaces the global exclusive lock with a concurrent-but-limited approach
_telegram_semaphore: Optional[asyncio.Semaphore] = None

# Per-channel semaphore to prevent concurrent operations on same channel
# Using OrderedDict as LRU cache with bounded size
_CHANNEL_LOCKS_MAX_SIZE = 100
_channel_locks: OrderedDict[str, asyncio.Lock] = OrderedDict()
_channel_locks_lock = asyncio.Lock()

# Singleton instance for shared collector
_shared_collector: Optional["TelegramCollector"] = None
_shared_collector_lock = asyncio.Lock()


def _get_telegram_semaphore() -> asyncio.Semaphore:
    """Get or create the Telegram operations semaphore."""
    global _telegram_semaphore
    if _telegram_semaphore is None:
        _telegram_semaphore = asyncio.Semaphore(settings.fetch_channel_semaphore)
    return _telegram_semaphore


async def _get_channel_lock(username: str) -> asyncio.Lock:
    """Get or create a lock for a specific channel.
    
    Uses LRU eviction to bound memory usage. Locks are evicted when
    the cache exceeds _CHANNEL_LOCKS_MAX_SIZE.
    """
    async with _channel_locks_lock:
        if username in _channel_locks:
            # Move to end (most recently used)
            _channel_locks.move_to_end(username)
        else:
            # Evict oldest entries if at capacity
            while len(_channel_locks) >= _CHANNEL_LOCKS_MAX_SIZE:
                _channel_locks.popitem(last=False)
            _channel_locks[username] = asyncio.Lock()
        return _channel_locks[username]


async def shutdown_collector() -> None:
    """Clean up collector resources on shutdown.
    
    Resets the global semaphore and clears channel locks to ensure
    a clean state for shutdown or restart.
    """
    global _telegram_semaphore, _shared_collector
    
    # Reset semaphore for clean restart
    _telegram_semaphore = None
    
    # Clear channel locks cache
    async with _channel_locks_lock:
        _channel_locks.clear()
    
    # Disconnect shared collector if exists
    async with _shared_collector_lock:
        if _shared_collector is not None:
            try:
                await _shared_collector.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting shared collector during shutdown: {e}")
            _shared_collector = None
    
    logger.info("Telegram collector shutdown complete")


class TelegramCollector:
    """Collector for fetching Telegram channel data with rate limiting.

    This class provides methods to fetch channel metadata and messages from
    Telegram channels. All methods use the @telegram_retry decorator to handle
    FloodWaitErrors with exponential backoff.

    Example:
        collector = TelegramCollector()
        try:
            channel_info = await collector.get_channel_info("durov")
            messages = await collector.get_recent_messages("durov", limit=20)
        finally:
            await collector.disconnect()
    """

    def __init__(self):
        self.api_id = settings.telegram_api_id
        self.api_hash = settings.telegram_api_hash
        self.phone = settings.telegram_phone
        self.client: Optional[TelegramClient] = None

    @staticmethod
    def _extract_message_data(message) -> dict | None:
        """Extract message data from a Telegram message object.

        Returns None if the message has no text content.
        """
        if not message.text:
            return None

        media_type = None
        media_urls = []

        if message.media:
            if hasattr(message.media, 'photo'):
                media_type = 'photo'
            elif hasattr(message.media, 'document'):
                media_type = 'document'
            elif hasattr(message.media, 'video'):
                media_type = 'video'

        return {
            'message_id': message.id,
            'text': message.text,
            'date': message.date,
            'media_type': media_type,
            'media_urls': media_urls,
        }

    async def connect(self):
        """Initialize and connect Telegram client.

        Uses a lock to prevent concurrent connection attempts (SQLite session file).
        Once connected, the client can handle multiple concurrent requests.
        """
        if self.client and self.client.is_connected():
            return self.client

        async with _connect_lock:
            # Double-check after acquiring lock
            if self.client and self.client.is_connected():
                return self.client

            if not self.client:
                # Store session files in data directory
                os.makedirs("data", exist_ok=True)
                self.client = TelegramClient("data/telegram_session", self.api_id, self.api_hash)

            await self.client.start(phone=self.phone)
            logger.info("Telegram client connected")
        return self.client

    async def disconnect(self):
        """Disconnect Telegram client."""
        if self.client:
            await self.client.disconnect()
            self.client = None
            logger.info("Telegram client disconnected")

    @telegram_retry
    async def get_channel_info(self, username: str) -> dict:
        """Fetch channel metadata from Telegram.

        Uses semaphore to limit concurrent operations while allowing parallelism.
        Automatically retries on FloodWaitError with exponential backoff.

        Args:
            username: Channel username (with or without @)

        Returns:
            Dict with channel info (id, title, username, description, participants_count)

        Raises:
            Exception: If channel cannot be fetched after retries
        """
        username = username.lstrip('@')
        channel_lock = await _get_channel_lock(username)

        async with _get_telegram_semaphore():
            async with channel_lock:
                await self.connect()

                logger.info(f"Fetching channel info for: {username}")

                # Get channel entity
                entity = await self.client.get_entity(username)

                # Get full channel info
                full_channel = await self.client(GetFullChannelRequest(entity))

                logger.info(f"Successfully fetched channel info for: {username}")

                return {
                    'id': entity.id,
                    'title': entity.title,
                    'username': entity.username or username,
                    'description': full_channel.full_chat.about or '',
                    'participants_count': full_channel.full_chat.participants_count or 0,
                }

    @telegram_retry
    async def get_recent_messages(self, username: str, limit: int = 50, offset_date=None) -> list:
        """Fetch recent messages from a channel.

        Uses semaphore to limit concurrent operations while allowing parallelism.
        Automatically retries on FloodWaitError with exponential backoff.

        Args:
            username: Channel username (with or without @)
            limit: Maximum number of messages to fetch
            offset_date: Optional datetime to start fetching from

        Returns:
            List of message dicts with id, text, date, media_type, media_urls
        """
        username = username.lstrip('@')
        channel_lock = await _get_channel_lock(username)

        async with _get_telegram_semaphore():
            async with channel_lock:
                await self.connect()

                logger.info(f"Fetching {limit} recent messages from: {username}")

                entity = await self.client.get_entity(username)

                messages = []
                async for message in self.client.iter_messages(entity, limit=limit, offset_date=offset_date):
                    msg_data = self._extract_message_data(message)
                    if msg_data:
                        messages.append(msg_data)

                logger.info(f"Fetched {len(messages)} messages from: {username}")
                return messages

    @telegram_retry
    async def get_messages_since(self, username: str, days: int | None = 7, max_messages: int | None = None) -> list:
        """Fetch messages from the last N days.

        Uses semaphore to limit concurrent operations while allowing parallelism.
        Automatically retries on FloodWaitError with exponential backoff.

        Args:
            username: Channel username (with or without @)
            days: Number of days to look back
            max_messages: Maximum number of messages to fetch

        Returns:
            List of message dicts with id, text, date, media_type, media_urls
        """
        username = username.lstrip('@')
        channel_lock = await _get_channel_lock(username)

        async with _get_telegram_semaphore():
            async with channel_lock:
                await self.connect()

                logger.info(f"Fetching messages from last {days} days for: {username}")

                entity = await self.client.get_entity(username)

                cutoff_date = None
                if days is not None:
                    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                messages = []

                async for message in self.client.iter_messages(entity, limit=max_messages):
                    # Stop if message is older than cutoff
                    msg_date = message.date
                    if msg_date is None:
                        # Skip messages without a date
                        continue
                    if msg_date.tzinfo is None:
                        msg_date = msg_date.replace(tzinfo=timezone.utc)
                    if cutoff_date and msg_date < cutoff_date:
                        break

                    msg_data = self._extract_message_data(message)
                    if msg_data:
                        messages.append(msg_data)

                logger.info(f"Fetched {len(messages)} messages from last {days} days for: {username}")
                return messages


async def get_shared_collector() -> TelegramCollector:
    """Get or create the shared TelegramCollector instance.

    This ensures only one collector is used across all requests,
    preventing SQLite session conflicts.
    """
    global _shared_collector
    async with _shared_collector_lock:
        if _shared_collector is None:
            _shared_collector = TelegramCollector()
        return _shared_collector


async def get_channel_info_with_lock(username: str) -> dict:
    """Get channel info with proper locking.

    Uses semaphore to limit concurrent operations while allowing parallelism.
    Uses per-channel lock to prevent concurrent operations on same channel.

    Args:
        username: Channel username (with or without @)

    Returns:
        Dict with channel info
    """
    username = username.lstrip('@')
    channel_lock = await _get_channel_lock(username)

    async with _get_telegram_semaphore():
        async with channel_lock:
            collector = await get_shared_collector()
            try:
                await collector.connect()

                logger.info(f"Fetching channel info for: {username} (with semaphore)")

                entity = await collector.client.get_entity(username)
                full_channel = await collector.client(GetFullChannelRequest(entity))

                logger.info(f"Successfully fetched channel info for: {username}")

                return {
                    'id': entity.id,
                    'title': entity.title,
                    'username': entity.username or username,
                    'description': full_channel.full_chat.about or '',
                    'participants_count': full_channel.full_chat.participants_count or 0,
                }
            except Exception as e:
                logger.error(f"Error fetching channel info for {username}: {e}")
                raise


async def fetch_historical_with_lock(username: str, days: int | None = 7, max_messages: int | None = None) -> list:
    """Fetch historical messages with proper locking around the entire operation.

    Uses semaphore to limit concurrent operations while allowing parallelism.
    Uses per-channel lock to prevent concurrent operations on same channel.

    Args:
        username: Channel username (with or without @)
        days: Number of days to look back
        max_messages: Maximum number of messages to fetch

    Returns:
        List of message dicts
    """
    username = username.lstrip('@')
    channel_lock = await _get_channel_lock(username)

    async with _get_telegram_semaphore():
        async with channel_lock:
            collector = await get_shared_collector()
            try:
                await collector.connect()

                days = None if not days else days
                log_range = "all available history" if days is None else f"last {days} days"
                logger.info(f"Fetching messages from {log_range} for: {username} (with semaphore)")

                entity = await collector.client.get_entity(username)

                cutoff_date = None
                if days is not None:
                    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                messages = []

                async for message in collector.client.iter_messages(entity, limit=max_messages):
                    msg_date = message.date
                    if msg_date is None:
                        # Skip messages without a date
                        continue
                    if msg_date.tzinfo is None:
                        msg_date = msg_date.replace(tzinfo=timezone.utc)
                    if cutoff_date and msg_date < cutoff_date:
                        break

                    msg_data = TelegramCollector._extract_message_data(message)
                    if msg_data:
                        messages.append(msg_data)

                logger.info(f"Fetched {len(messages)} messages from {log_range} for: {username}")
                return messages
            except Exception as e:
                logger.error(f"Error fetching historical messages for {username}: {e}")
                raise

    async def iter_historical_messages(self, username: str, offset_id: int = 0, batch_size: int = 50, days: int | None = 7):
        """Iterate over historical messages in batches, starting from offset_id.
        
        This generator yields batches of messages. It DOES NOT handle FloodWaitError internally
        to allow the caller to pause/resume the job state properly.
        
        Args:
            username: Channel username
            offset_id: ID of the last processed message (0 for start)
            batch_size: Number of messages to yield per batch
            days: Number of days to look back
        
        Yields:
            List[dict]: Batch of message data
        """
        username = username.lstrip('@')
        # Note: We assume the caller handles connection/locking via iter_historical_with_lock wrapper
        
        logger.info(f"Starting streaming fetch for {username} (start_id={offset_id})")
        
        entity = await self.client.get_entity(username)
        
        cutoff_date = None
        if days is not None:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
        current_batch = []
        
        # iter_messages iterates from NEWEST to OLDEST by default.
        # offset_id in telethon (min_id/max_id) logic:
        # We want to continue from where we left off. 
        # If we are iterating NEWEST -> OLDEST, 'offset_id' usually means "start after this ID" 
        # but pure offset_id in telethon often shifts the window.
        # For seamless resumption on "newest to oldest" fetch:
        # We need to use 'max_id' argument if we want messages OLDER than a certain ID.
        # If offset_id == 0, we start from top (no max_id).
        # If offset_id > 0, we use max_id = offset_id (excluding it) to get older messages.
        
        kwargs = {'limit': None} # Unlimited iteration, we control via break
        if offset_id > 0:
            kwargs['max_id'] = offset_id
            
        async for message in self.client.iter_messages(entity, **kwargs):
            msg_date = message.date
            if msg_date is None:
                continue
            if msg_date.tzinfo is None:
                msg_date = msg_date.replace(tzinfo=timezone.utc)
            
            if cutoff_date and msg_date < cutoff_date:
                # Reached time limit
                break
                
            msg_data = self._extract_message_data(message)
            if msg_data:
                current_batch.append(msg_data)
                
            if len(current_batch) >= batch_size:
                yield current_batch
                current_batch = []
                
        # Yield remaining
        if current_batch:
            yield current_batch


async def iter_historical_with_lock(username: str, offset_id: int = 0, batch_size: int = 50, days: int | None = 7):
    """Wrapper to iterate historical messages with lock.
    
    WARNING: This yields control back to the caller while holding an async generator.
    The lock is held during the *setup* but technically released if we yield? 
    No, async generators context managers are tricky. 
    Ideally we want the lock held for the duration of the iteration?
    Actually, holding the global semaphore for the entire duration of a long fetch (streaming) 
    might block other channels too much if we have many.
    
     BETTER STRATEGY to handle FloodWait at caller level:
    We should probably acquire the lock for *each batch* or keep it if we want strict serialization.
    For simplicity and safety, we will hold the channel lock and semaphore for the generator lifespan.
    """
    username = username.lstrip('@')
    channel_lock = await _get_channel_lock(username)

    async with _get_telegram_semaphore():
        async with channel_lock:
            collector = await get_shared_collector()
            await collector.connect()
            
            # Forward the generator
            async for batch in collector.iter_historical_messages(username, offset_id, batch_size, days):
                yield batch
