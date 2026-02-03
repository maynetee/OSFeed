"""Channel Utility Functions

Shared helper functions for channel handling across API endpoints and services.
"""

import re
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.channel import Channel, user_channels


def clean_channel_username(username: str) -> str:
    """Clean and normalize a Telegram channel username.

    Removes common URL prefixes and formatting characters from channel usernames
    to produce a clean username suitable for Telegram API calls.

    Args:
        username: Raw username string that may contain URLs or @ prefix

    Returns:
        Cleaned username without URL prefixes or @ symbol

    Examples:
        >>> clean_channel_username("https://t.me/example")
        'example'
        >>> clean_channel_username("@example")
        'example'
        >>> clean_channel_username("  example  ")
        'example'
    """
    # Strip whitespace
    username = username.strip()

    # Remove URL prefixes
    if username.startswith("https://t.me/"):
        username = username.replace("https://t.me/", "")
    if username.startswith("t.me/"):
        username = username.replace("t.me/", "")

    # Remove @ prefix
    username = username.lstrip("@")

    return username


def validate_channel_username(username: str) -> bool:
    """Validate a Telegram channel username format.

    Checks if a username meets Telegram's username requirements:
    - 5-32 characters total
    - Must start with a letter
    - Can contain letters, numbers, and underscores
    - Must end with a letter or number (not underscore)

    Args:
        username: Cleaned username to validate (should be cleaned first with clean_channel_username)

    Returns:
        True if username is valid, False otherwise

    Examples:
        >>> validate_channel_username("example")
        True
        >>> validate_channel_username("ex")
        False
        >>> validate_channel_username("123invalid")
        False
    """
    if not username:
        return False

    # Telegram username pattern: 5-32 chars, starts with letter, ends with letter/digit
    pattern = r"^[a-zA-Z][\w\d]{3,30}[a-zA-Z\d]$"
    return bool(re.match(pattern, username))


async def get_existing_channel(db: AsyncSession, username: str) -> Optional[Channel]:
    """Get an existing channel from the database by username.

    Queries the database to find a channel with the given username.
    Returns the channel if found, or None if it doesn't exist.

    Args:
        db: Active database session
        username: Cleaned channel username (should be cleaned with clean_channel_username first)

    Returns:
        Channel object if found, None otherwise

    Examples:
        >>> channel = await get_existing_channel(db, "example_channel")
        >>> if channel:
        ...     print(f"Found: {channel.title}")
        ... else:
        ...     print("Channel not found")
    """
    result = await db.execute(
        select(Channel).where(Channel.username == username)
    )
    return result.scalar_one_or_none()


async def check_user_channel_link(db: AsyncSession, user_id: UUID, channel_id: UUID) -> bool:
    """Check if a user has a link to a specific channel.

    Queries the user_channels association table to determine if a user
    is already linked to a channel.

    Args:
        db: Active database session
        user_id: UUID of the user
        channel_id: UUID of the channel

    Returns:
        True if the user has a link to the channel, False otherwise

    Examples:
        >>> has_link = await check_user_channel_link(db, user.id, channel.id)
        >>> if has_link:
        ...     print("User already has this channel")
        ... else:
        ...     print("User doesn't have this channel yet")
    """
    result = await db.execute(
        select(user_channels).where(
            and_(
                user_channels.c.user_id == user_id,
                user_channels.c.channel_id == channel_id
            )
        )
    )
    existing_link = result.first()
    return existing_link is not None


async def resolve_and_join_telegram_channel(telegram_client, username: str) -> dict:
    """Resolve and join a Telegram channel, returning channel information.

    Connects to Telegram to resolve channel details, joins the channel,
    and records the join operation. This is used when adding a new channel
    that doesn't exist in the database yet.

    Args:
        telegram_client: Active Telegram client instance
        username: Cleaned channel username (should be cleaned with clean_channel_username first)

    Returns:
        Dictionary containing channel information with keys:
        - telegram_id: Telegram's unique ID for the channel
        - title: Channel display title
        - description: Channel description (may be None)
        - subscribers: Number of subscribers (defaults to 0)

    Raises:
        ValueError: If the channel cannot be resolved (invalid username, private channel, etc.)

    Examples:
        >>> from app.services.telegram_client import get_telegram_client
        >>> telegram_client = get_telegram_client()
        >>> channel_info = await resolve_and_join_telegram_channel(telegram_client, "example_channel")
        >>> print(channel_info['title'])
    """
    # Resolve and join channel via Telegram
    channel_info = await telegram_client.resolve_channel(username)
    await telegram_client.join_public_channel(username)
    await telegram_client.record_channel_join()

    return channel_info
