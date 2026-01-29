"""Unit tests for should_channel_translate function.

Tests the channel translation decision logic that determines whether
messages from a channel need translation based on user language preferences.
"""

import uuid

import pytest
from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.models.channel import Channel, user_channels
from app.models.user import User
from app.services.translation_service import should_channel_translate
from fastapi_users.password import PasswordHelper


async def _create_user_with_language(
    email: str, preferred_language: str = "en"
) -> User:
    """Create a test user with a specific preferred language."""
    password_helper = PasswordHelper()
    async with AsyncSessionLocal() as session:
        user = User(
            email=email,
            hashed_password=password_helper.hash("password123"),
            is_active=True,
            is_superuser=False,
            is_verified=True,
            preferred_language=preferred_language,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_channel(
    username: str, title: str, detected_language: str = None
) -> Channel:
    """Create a test channel with a specific detected language."""
    async with AsyncSessionLocal() as session:
        channel = Channel(
            id=uuid.uuid4(),
            username=username,
            title=title,
            detected_language=detected_language,
        )
        session.add(channel)
        await session.commit()
        await session.refresh(channel)
        return channel


async def _link_user_to_channel(user_id: uuid.UUID, channel_id: uuid.UUID) -> None:
    """Link a user to a channel via the user_channels junction table."""
    async with AsyncSessionLocal() as session:
        await session.execute(
            user_channels.insert().values(user_id=user_id, channel_id=channel_id)
        )
        await session.commit()


@pytest.mark.asyncio
async def test_should_channel_translate_homogeneous_users_returns_false() -> None:
    """When all users share the channel's language, translation is not needed."""
    await init_db()

    unique_id = uuid.uuid4().hex[:8]
    channel = await _create_channel(
        username=f"french_channel_{unique_id}",
        title="French Channel",
        detected_language="fr",
    )

    # Create two French-speaking users
    user1 = await _create_user_with_language(
        email=f"user1_fr_{unique_id}@example.com",
        preferred_language="fr",
    )
    user2 = await _create_user_with_language(
        email=f"user2_fr_{unique_id}@example.com",
        preferred_language="fr",
    )

    # Link both users to the channel
    await _link_user_to_channel(user1.id, channel.id)
    await _link_user_to_channel(user2.id, channel.id)

    # Should return False - no translation needed
    result = await should_channel_translate(channel.id)
    assert result is False


@pytest.mark.asyncio
async def test_should_channel_translate_mixed_users_returns_true() -> None:
    """When any user has a different language, translation is needed."""
    await init_db()

    unique_id = uuid.uuid4().hex[:8]
    channel = await _create_channel(
        username=f"english_channel_{unique_id}",
        title="English Channel",
        detected_language="en",
    )

    # Create one English-speaking user and one French-speaking user
    user1 = await _create_user_with_language(
        email=f"user1_en_{unique_id}@example.com",
        preferred_language="en",
    )
    user2 = await _create_user_with_language(
        email=f"user2_fr_{unique_id}@example.com",
        preferred_language="fr",
    )

    # Link both users to the channel
    await _link_user_to_channel(user1.id, channel.id)
    await _link_user_to_channel(user2.id, channel.id)

    # Should return True - translation needed for the French user
    result = await should_channel_translate(channel.id)
    assert result is True


@pytest.mark.asyncio
async def test_should_channel_translate_no_users_returns_true() -> None:
    """When no users have added the channel, default to translating."""
    await init_db()

    unique_id = uuid.uuid4().hex[:8]
    channel = await _create_channel(
        username=f"orphan_channel_{unique_id}",
        title="Orphan Channel",
        detected_language="es",
    )

    # No users linked to channel - should default to translation
    result = await should_channel_translate(channel.id)
    assert result is True


@pytest.mark.asyncio
async def test_should_channel_translate_null_channel_language_returns_true() -> None:
    """When channel has no detected_language, default to translating."""
    await init_db()

    unique_id = uuid.uuid4().hex[:8]
    channel = await _create_channel(
        username=f"unknown_lang_channel_{unique_id}",
        title="Unknown Language Channel",
        detected_language=None,  # No detected language
    )

    # Add a user to the channel
    user = await _create_user_with_language(
        email=f"user_unknown_{unique_id}@example.com",
        preferred_language="en",
    )
    await _link_user_to_channel(user.id, channel.id)

    # Should return True - no channel language means we translate
    result = await should_channel_translate(channel.id)
    assert result is True


@pytest.mark.asyncio
async def test_should_channel_translate_single_matching_user_returns_false() -> None:
    """When single user matches channel language, no translation needed."""
    await init_db()

    unique_id = uuid.uuid4().hex[:8]
    channel = await _create_channel(
        username=f"german_channel_{unique_id}",
        title="German Channel",
        detected_language="de",
    )

    # Create one German-speaking user
    user = await _create_user_with_language(
        email=f"user_de_{unique_id}@example.com",
        preferred_language="de",
    )
    await _link_user_to_channel(user.id, channel.id)

    # Should return False - single user matches
    result = await should_channel_translate(channel.id)
    assert result is False


@pytest.mark.asyncio
async def test_should_channel_translate_nonexistent_channel_returns_true() -> None:
    """When channel doesn't exist, default to translating (safe fallback)."""
    await init_db()

    nonexistent_channel_id = uuid.uuid4()

    # Should return True - channel not found defaults to translate
    result = await should_channel_translate(nonexistent_channel_id)
    assert result is True


@pytest.mark.asyncio
async def test_should_channel_translate_single_mismatched_user_returns_true() -> None:
    """When single user differs from channel language, translation needed."""
    await init_db()

    unique_id = uuid.uuid4().hex[:8]
    channel = await _create_channel(
        username=f"russian_channel_{unique_id}",
        title="Russian Channel",
        detected_language="ru",
    )

    # Create one English-speaking user (different from channel)
    user = await _create_user_with_language(
        email=f"user_en_ru_{unique_id}@example.com",
        preferred_language="en",
    )
    await _link_user_to_channel(user.id, channel.id)

    # Should return True - user language differs from channel
    result = await should_channel_translate(channel.id)
    assert result is True


@pytest.mark.asyncio
async def test_should_channel_translate_multiple_users_one_mismatch_returns_true() -> None:
    """When multiple users exist and one mismatches, translation is needed."""
    await init_db()

    unique_id = uuid.uuid4().hex[:8]
    channel = await _create_channel(
        username=f"portuguese_channel_{unique_id}",
        title="Portuguese Channel",
        detected_language="pt",
    )

    # Create multiple Portuguese users and one English user
    users_pt = []
    for i in range(3):
        user = await _create_user_with_language(
            email=f"user_pt_{i}_{unique_id}@example.com",
            preferred_language="pt",
        )
        users_pt.append(user)
        await _link_user_to_channel(user.id, channel.id)

    # Add one English user
    user_en = await _create_user_with_language(
        email=f"user_en_pt_{unique_id}@example.com",
        preferred_language="en",
    )
    await _link_user_to_channel(user_en.id, channel.id)

    # Should return True - one user has different language
    result = await should_channel_translate(channel.id)
    assert result is True
