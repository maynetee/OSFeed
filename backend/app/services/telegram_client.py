"""Telegram Client Manager for OSFeed.

Provides a singleton Telegram client with:
- Session persistence
- Rate limiting via Redis token bucket
- FloodWait error handling
- JoinChannel daily quota tracking
- Channel resolution and joining
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest, GetFullChannelRequest
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.types import Channel as TelegramChannel
from telethon.errors import (
    FloodWaitError,
    ChannelPrivateError,
    UsernameNotOccupiedError,
    UsernameInvalidError,
    ChannelInvalidError,
)

from app.config import settings
from app.services.rate_limiter import get_rate_limiter, RedisTokenBucket

logger = logging.getLogger(__name__)


class TelegramClientManager:
    """Singleton manager for Telegram client.

    Handles:
    - Session management and persistence
    - Rate limiting via Redis token bucket
    - FloodWait error handling with exponential backoff
    - JoinChannel daily quota tracking
    """

    def __init__(self):
        self._client: Optional[TelegramClient] = None
        self._rate_limiter: Optional[RedisTokenBucket] = None
        self._connected = False
        self._lock = asyncio.Lock()

    async def _ensure_connected(self) -> TelegramClient:
        """Ensure client is connected, creating it if needed."""
        async with self._lock:
            if self._client is None or not self._connected:
                if not settings.telegram_api_id or not settings.telegram_api_hash:
                    raise RuntimeError(
                        "Telegram credentials not configured. "
                        "Set TELEGRAM_API_ID and TELEGRAM_API_HASH environment variables."
                    )

                # Use StringSession if provided (for cloud deployments)
                # Otherwise fall back to file-based session
                if settings.telegram_session_string:
                    logger.info("Using StringSession from environment")
                    session = StringSession(settings.telegram_session_string)
                else:
                    session = settings.telegram_session_path
                    if session.endswith(".session"):
                        session = session[:-8]
                    logger.info(f"Using file-based session at {session}")

                self._client = TelegramClient(
                    session,
                    settings.telegram_api_id,
                    settings.telegram_api_hash
                )

                await self._client.connect()

                if not await self._client.is_user_authorized():
                    raise RuntimeError(
                        "Telegram session not authorized. "
                        "Run 'python -m app.cli.telegram_setup' to authenticate."
                    )

                self._connected = True
                logger.info("Telegram client connected and authorized")

            return self._client

    async def get_client(self) -> TelegramClient:
        """Get the Telegram client, connecting if needed."""
        return await self._ensure_connected()

    def _get_rate_limiter(self) -> RedisTokenBucket:
        """Get rate limiter instance."""
        if self._rate_limiter is None:
            self._rate_limiter = get_rate_limiter()
        return self._rate_limiter

    async def acquire_rate_limit(self, tokens: int = 1) -> None:
        """Acquire rate limit tokens, waiting if necessary.

        Raises:
            RuntimeError: If rate limit cannot be acquired within timeout
        """
        rate_limiter = self._get_rate_limiter()
        acquired = await rate_limiter.acquire_with_wait(
            tokens=tokens,
            max_wait=60.0  # Wait up to 60 seconds
        )
        if not acquired:
            raise RuntimeError("Rate limit exceeded, could not acquire tokens")

    async def can_join_channel(self) -> bool:
        """Check if we can join another channel today."""
        rate_limiter = self._get_rate_limiter()
        return await rate_limiter.can_join_channel(
            settings.telegram_join_channel_daily_limit
        )

    async def record_channel_join(self) -> int:
        """Record a channel join, return new daily count."""
        rate_limiter = self._get_rate_limiter()
        return await rate_limiter.increment_join_count()

    async def resolve_channel(self, username: str) -> Dict[str, Any]:
        """Resolve channel username to entity info.

        Args:
            username: Channel username (without @)

        Returns:
            Dict with telegram_id, title, username, description, subscribers

        Raises:
            ValueError: For invalid or private channels
        """
        await self.acquire_rate_limit()
        client = await self.get_client()

        # Clean username
        username = username.lstrip("@")

        try:
            result = await client(ResolveUsernameRequest(username))

            if not result.chats:
                raise ValueError(f"No channel found for username: {username}")

            entity = result.chats[0]

            if not isinstance(entity, TelegramChannel):
                raise ValueError(f"{username} is not a channel")

            # Get full channel info for description and subscriber count
            await self.acquire_rate_limit()
            full_channel = await client(GetFullChannelRequest(entity))

            return {
                "telegram_id": entity.id,
                "title": entity.title,
                "username": entity.username,
                "description": full_channel.full_chat.about or "",
                "subscribers": full_channel.full_chat.participants_count or 0,
            }

        except UsernameNotOccupiedError:
            raise ValueError(f"Username not found: {username}")
        except UsernameInvalidError:
            raise ValueError(f"Invalid username format: {username}")
        except ChannelPrivateError:
            raise ValueError(f"Channel is private: {username}")
        except ChannelInvalidError:
            raise ValueError(f"Invalid channel: {username}")
        except FloodWaitError as e:
            logger.warning(f"FloodWait: need to wait {e.seconds}s")
            await asyncio.sleep(e.seconds * settings.telegram_flood_wait_multiplier)
            # Retry once after waiting
            return await self.resolve_channel(username)

    async def join_public_channel(self, username: str) -> bool:
        """Join a public channel to enable message fetching.

        Args:
            username: Channel username (without @)

        Returns:
            True if successfully joined

        Raises:
            ValueError: For private or invalid channels
        """
        await self.acquire_rate_limit()
        client = await self.get_client()

        username = username.lstrip("@")

        try:
            await client(JoinChannelRequest(username))
            logger.info(f"Joined channel: @{username}")
            return True

        except ChannelPrivateError:
            raise ValueError(f"Cannot join private channel: {username}")
        except UsernameNotOccupiedError:
            raise ValueError(f"Channel not found: {username}")
        except FloodWaitError as e:
            logger.warning(f"FloodWait on join: need to wait {e.seconds}s")
            await asyncio.sleep(e.seconds * settings.telegram_flood_wait_multiplier)
            return await self.join_public_channel(username)

    async def get_messages(
        self,
        channel_username: str,
        limit: int = 100,
        min_id: int = 0,
        offset_date: Optional[datetime] = None
    ) -> List[Any]:
        """Fetch messages from a channel.

        Args:
            channel_username: Channel username
            limit: Maximum messages to fetch (default 100)
            min_id: Only get messages after this ID (for incremental sync)
            offset_date: Only get messages before this date

        Returns:
            List of Telethon message objects
        """
        await self.acquire_rate_limit()
        client = await self.get_client()

        try:
            messages = await client.get_messages(
                channel_username,
                limit=limit,
                min_id=min_id,
                offset_date=offset_date
            )
            return list(messages)

        except FloodWaitError as e:
            logger.warning(f"FloodWait on get_messages: waiting {e.seconds}s")
            await asyncio.sleep(e.seconds * settings.telegram_flood_wait_multiplier)
            return await self.get_messages(channel_username, limit, min_id, offset_date)
        except ChannelPrivateError:
            logger.error(f"Cannot access private channel: {channel_username}")
            return []

    async def disconnect(self) -> None:
        """Disconnect the client gracefully."""
        async with self._lock:
            if self._client and self._connected:
                await self._client.disconnect()
                self._connected = False
                logger.info("Telegram client disconnected")


# Singleton instance
_telegram_manager: Optional[TelegramClientManager] = None


def get_telegram_client() -> TelegramClientManager:
    """Get the singleton Telegram client manager."""
    global _telegram_manager
    if _telegram_manager is None:
        _telegram_manager = TelegramClientManager()
    return _telegram_manager


async def cleanup_telegram_client() -> None:
    """Cleanup Telegram client on shutdown."""
    global _telegram_manager
    if _telegram_manager:
        await _telegram_manager.disconnect()
        _telegram_manager = None
