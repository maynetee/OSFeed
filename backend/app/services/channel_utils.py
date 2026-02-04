"""Channel Utility Functions

Shared helper functions for channel handling across API endpoints and services.
"""

import re
from typing import Optional, Literal, TypedDict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, insert

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


async def get_authorized_channel(db: AsyncSession, channel_id: UUID, user_id: UUID) -> Optional[Channel]:
    """Get a channel by ID with user authorization check.

    Queries the database for a channel that the user has access to.
    Returns the channel if found and user has permission, None otherwise.

    Args:
        db: Active database session
        channel_id: UUID of the channel
        user_id: UUID of the user

    Returns:
        Channel object if found and user has access, None otherwise

    Examples:
        >>> channel = await get_authorized_channel(db, channel_id, user.id)
        >>> if channel:
        ...     print(f"User has access to {channel.title}")
        ... else:
        ...     print("Channel not found or access denied")
    """
    result = await db.execute(
        select(Channel).join(
            user_channels,
            and_(user_channels.c.channel_id == Channel.id, user_channels.c.user_id == user_id)
        ).where(Channel.id == channel_id)
    )
    return result.scalar_one_or_none()


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


async def auto_assign_to_collections(db: AsyncSession, user_id: UUID, channel: Channel) -> None:
    """Automatically assign a channel to user's collections based on rules.

    Evaluates all collections for a user and automatically adds the channel
    to collections that match auto-assignment criteria:
    - Default collections (always added)
    - Language-based matching (if channel language matches collection's auto_assign_languages)
    - Keyword-based matching (if collection keywords appear in channel title/description)
    - Tag-based matching (if channel tags match collection's auto_assign_tags)

    Global collections are always skipped. Duplicate assignments are prevented
    by checking if the channel is already in the collection.

    Args:
        db: Active database session
        user_id: UUID of the user whose collections should be evaluated
        channel: Channel object to be assigned to collections

    Returns:
        None. Collections are modified in place via the ORM relationship.

    Examples:
        >>> # After creating or linking a channel for a user
        >>> await auto_assign_to_collections(db, user.id, channel)
        >>> await db.commit()  # Don't forget to commit after calling this
    """
    from sqlalchemy.orm import selectinload
    from app.models.collection import Collection

    # Fetch all collections for the user with channels preloaded
    collections_result = await db.execute(
        select(Collection)
        .options(selectinload(Collection.channels))
        .where(Collection.user_id == user_id)
    )
    collections = collections_result.scalars().all()

    # Prepare channel data for matching
    channel_lang = channel.detected_language
    search_text = f"{channel.title} {channel.description or ''}".lower()

    for collection in collections:
        # Check if already in collection to avoid dupes
        if channel in collection.channels:
            continue

        # Skip global collections
        if collection.is_global:
            continue

        # Add to default collections
        if collection.is_default:
            collection.channels.append(channel)
            continue

        # Check language-based auto-assignment
        if collection.auto_assign_languages and channel_lang:
            if channel_lang in (collection.auto_assign_languages or []):
                collection.channels.append(channel)
                continue

        # Check keyword-based auto-assignment
        if collection.auto_assign_keywords:
            if any(keyword.lower() in search_text for keyword in collection.auto_assign_keywords or []):
                collection.channels.append(channel)
                continue

        # Check tag-based auto-assignment
        if collection.auto_assign_tags and channel.tags:
            if any(tag in (collection.auto_assign_tags or []) for tag in channel.tags):
                collection.channels.append(channel)


class ProcessChannelAddResult(TypedDict):
    """Result of processing a channel add operation.

    Attributes:
        success: True if channel was added/linked successfully
        channel: Channel object if successful, None otherwise
        is_new: True if channel was newly created, False if existing
        error: Error message if unsuccessful
        error_code: Specific error code for programmatic handling
        job: Fetch job info dictionary if created, None otherwise
    """
    success: bool
    channel: Optional[Channel]
    is_new: bool
    error: Optional[str]
    error_code: Optional[str]
    job: Optional[dict]


async def process_channel_add(
    db: AsyncSession,
    user_id: UUID,
    username: str,
    error_mode: Literal["raise", "return"] = "raise",
) -> ProcessChannelAddResult:
    """Process adding a channel for a user.

    This is the shared logic used by both single and bulk channel add endpoints.
    Handles channel existence checking, Telegram resolution, collection assignment,
    audit logging, and fetch job creation.

    The username must already be cleaned and validated before calling this function.

    Args:
        db: Active database session
        user_id: UUID of the user adding the channel
        username: Cleaned channel username (must already be cleaned and validated)
        error_mode: How to handle errors:
            - 'raise': Raise HTTPException (for single endpoint)
            - 'return': Return result with error details (for bulk endpoint)

    Returns:
        ProcessChannelAddResult dictionary containing:
        - success: True if channel was added/linked successfully
        - channel: Channel object if successful, None otherwise
        - is_new: True if channel was newly created, False if existing
        - error: Error message if unsuccessful
        - error_code: Specific error code for programmatic handling
        - job: Fetch job info dict if created, None otherwise

    Raises:
        HTTPException: Only when error_mode='raise' and an error occurs

    Notes:
        - Caller is responsible for calling db.commit() or db.flush() after this function
        - For single endpoint: call db.commit() after this function returns
        - For bulk endpoint: call db.flush() after this function, then db.commit() after all channels
        - The channel object returned needs db.refresh() if you've called flush/commit

    Examples:
        >>> # Single endpoint usage (error_mode='raise')
        >>> result = await process_channel_add(db, user.id, "example_channel", error_mode="raise")
        >>> await db.commit()
        >>> await db.refresh(result['channel'])

        >>> # Bulk endpoint usage (error_mode='return')
        >>> result = await process_channel_add(db, user.id, "example_channel", error_mode="return")
        >>> if result['success']:
        ...     await db.flush()
        ...     await db.refresh(result['channel'])
        ...     # Add to succeeded list
        >>> else:
        ...     # Add to failed list with result['error']
    """
    from fastapi import HTTPException
    from app.services.telegram_client import get_telegram_client
    from app.services.audit import record_audit_event
    from app.services.fetch_queue import enqueue_fetch_job
    from app.services.channel_join_queue import queue_channel_join
    from app.config import settings
    from sqlalchemy.exc import SQLAlchemyError, IntegrityError
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Check if channel already exists
        existing_channel = await get_existing_channel(db, username)

        channel_to_use = None
        is_new = False

        if existing_channel:
            # Check if user already has this channel
            has_link = await check_user_channel_link(db, user_id, existing_channel.id)

            if has_link:
                # Link exists
                if not existing_channel.is_active:
                    # Reactivate the channel
                    existing_channel.is_active = True
                    channel_to_use = existing_channel
                else:
                    # Channel is active and linked - already in user's list
                    error_msg = "Channel already exists in your list"
                    if error_mode == "raise":
                        raise HTTPException(status_code=400, detail=error_msg)
                    return {
                        "success": False,
                        "channel": None,
                        "is_new": False,
                        "error": error_msg,
                        "error_code": "ALREADY_EXISTS",
                        "job": None,
                    }
            else:
                # Channel exists but user doesn't have it linked yet
                if not existing_channel.is_active:
                    existing_channel.is_active = True

                await db.execute(
                    insert(user_channels).values(
                        user_id=user_id,
                        channel_id=existing_channel.id
                    )
                )
                channel_to_use = existing_channel
        else:
            # Channel doesn't exist - create via Telegram
            telegram_client = get_telegram_client()

            # Check JoinChannel limit before proceeding
            if not await telegram_client.can_join_channel():
                if settings.telegram_join_channel_queue_enabled:
                    # Queue for later processing
                    await queue_channel_join(username, user_id)
                    error_msg = "Daily channel join limit reached. Your request has been queued." if error_mode == "raise" else "Daily channel join limit reached. Request has been queued."
                    if error_mode == "raise":
                        raise HTTPException(status_code=202, detail="Daily channel join limit reached. Your request has been queued.")
                    return {
                        "success": False,
                        "channel": None,
                        "is_new": False,
                        "error": "Daily channel join limit reached. Request has been queued.",
                        "error_code": "RATE_LIMITED_QUEUED",
                        "job": None,
                    }
                else:
                    error_msg = "Daily channel join limit reached. Please try again tomorrow."
                    if error_mode == "raise":
                        raise HTTPException(status_code=429, detail=error_msg)
                    return {
                        "success": False,
                        "channel": None,
                        "is_new": False,
                        "error": error_msg,
                        "error_code": "RATE_LIMITED",
                        "job": None,
                    }

            try:
                # Resolve and join channel via Telegram
                channel_info = await resolve_and_join_telegram_channel(telegram_client, username)

                # Create new channel record
                channel_to_use = Channel(
                    username=username,
                    telegram_id=channel_info['telegram_id'],
                    title=channel_info['title'],
                    description=channel_info.get('description'),
                    subscriber_count=channel_info.get('subscribers', 0),
                    is_active=True
                )
                db.add(channel_to_use)
                is_new = True

            except ValueError as e:
                # Invalid username, private channel, etc.
                logger.warning(f"Failed to resolve/join channel '{username}': {e}")
                error_msg = "Unable to add channel. It may be private or invalid."
                if error_mode == "raise":
                    raise HTTPException(status_code=400, detail=error_msg)
                return {
                    "success": False,
                    "channel": None,
                    "is_new": False,
                    "error": error_msg,
                    "error_code": "TELEGRAM_ERROR",
                    "job": None,
                }

        # Assign to collections (for both new and existing linked channels)
        await auto_assign_to_collections(db, user_id, channel_to_use)

        # Record audit event
        record_audit_event(
            db,
            user_id=user_id,
            action="channel.create" if is_new else "channel.link",
            resource_type="channel",
            resource_id=str(channel_to_use.id),
            metadata={"username": username, "is_new": is_new},
        )

        # Note: Caller should handle commit/flush/refresh as appropriate
        # For single endpoint: commit happens after this
        # For bulk endpoint: flush happens after this, commit after all channels

        # Enqueue fetch job (enqueue_fetch_job handles deduplication if already running)
        job = await enqueue_fetch_job(channel_to_use.id, channel_to_use.username, days=7)

        job_dict = None
        if job:
            from app.schemas.fetch_job import FetchJobStatus
            job_dict = FetchJobStatus.model_validate(job).model_dump()

        return {
            "success": True,
            "channel": channel_to_use,
            "is_new": is_new,
            "error": None,
            "error_code": None,
            "job": job_dict,
        }

    except HTTPException:
        # Re-raise HTTPExceptions (for error_mode='raise')
        raise
    except (SQLAlchemyError, IntegrityError) as e:
        logger.error(f"Database error adding channel '{username}' for user {user_id}: {type(e).__name__}: {e}", exc_info=True)
        error_msg = "Failed to add channel due to a database error."
        if error_mode == "raise":
            raise HTTPException(status_code=500, detail="CHANNEL_ADD_DATABASE_ERROR")
        return {
            "success": False,
            "channel": None,
            "is_new": False,
            "error": error_msg,
            "error_code": "DATABASE_ERROR",
            "job": None,
        }
    except Exception as e:
        logger.error(f"Unexpected error adding channel '{username}' for user {user_id}: {type(e).__name__}: {e}", exc_info=True)
        error_msg = "Failed to add channel due to an internal error."
        if error_mode == "raise":
            raise HTTPException(status_code=500, detail="CHANNEL_ADD_ERROR")
        return {
            "success": False,
            "channel": None,
            "is_new": False,
            "error": error_msg,
            "error_code": "INTERNAL_ERROR",
            "job": None,
        }
