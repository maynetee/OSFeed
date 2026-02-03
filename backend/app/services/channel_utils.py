"""Channel Utility Functions

Shared helper functions for channel handling across API endpoints and services.
"""

import re
from typing import Optional


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
