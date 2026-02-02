from uuid import UUID, uuid4
from types import SimpleNamespace
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi_users.password import PasswordHelper
from sqlalchemy import text, select

from app.main import app
from app.database import AsyncSessionLocal, init_db
from app.models.channel import Channel
from app.models.message import Message
from app.models.user import User
from app.auth.users import current_active_user


async def _create_user(email: str, password: str) -> User:
    """Create a test user and return the User object."""
    password_helper = PasswordHelper()
    user_id = uuid4()
    async with AsyncSessionLocal() as session:
        # Create user directly with ORM to ensure proper UUID handling
        user = User(
            id=user_id,
            email=email,
            hashed_password=password_helper.hash(password),
            is_active=True,
            is_superuser=False,
            is_verified=True,
            role="viewer",
            data_retention_days=365,
            preferred_language="en",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_channel_for_user(user_id, username: str) -> Channel:
    """Create a channel and link it to a user."""
    async with AsyncSessionLocal() as session:
        # Use hash of username to generate unique telegram_id
        telegram_id = hash(username) % 1000000000
        channel = Channel(
            username=username,
            telegram_id=telegram_id,
            title=f"Test Channel {username}",
            description="Test description",
            subscriber_count=1000,
            is_active=True,
        )
        session.add(channel)
        await session.flush()
        user_id_str = str(user_id)
        await session.execute(
            text(
                "INSERT INTO user_channels (id, user_id, channel_id, added_at) "
                "VALUES (:id, :user_id, :channel_id, :added_at)"
            ),
            {
                "id": str(uuid4()),
                "user_id": user_id_str,
                "channel_id": channel.id.hex,
                "added_at": None,
            },
        )
        await session.commit()
        await session.refresh(channel)
        return channel


async def _create_message_for_channel(channel_id: UUID, text: str = "Test message") -> Message:
    """Create a message for a specific channel."""
    async with AsyncSessionLocal() as session:
        message = Message(
            channel_id=channel_id,
            telegram_message_id=12345,
            original_text=text,
            translated_text=None,
            needs_translation=False,
            published_at=datetime.now(timezone.utc),
        )
        session.add(message)
        await session.commit()
        await session.refresh(message)
        return message


# Test get_channel endpoint


@pytest.mark.asyncio
async def test_get_channel_unauthorized_access():
    """Test that user A cannot access user B's channel."""
    await init_db()

    # Create user A with a channel
    user_a = await _create_user("user_a_channel@example.com", "password123")
    channel_a = await _create_channel_for_user(user_a.id, "user_a_channel")

    # Create user B
    user_b = await _create_user("user_b_channel@example.com", "password123")

    # User B tries to access user A's channel
    async def _override_user():
        return user_b

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/channels/{channel_a.id}")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Should return 404 (not 403) to avoid information leakage
    assert response.status_code == 404
    assert response.json()["detail"] == "Channel not found"


@pytest.mark.asyncio
async def test_get_channel_authorized_access():
    """Test that user A can access their own channel."""
    await init_db()

    # Create user A with a channel
    user_a = await _create_user("user_a_own@example.com", "password123")
    channel_a = await _create_channel_for_user(user_a.id, "user_a_own_channel")

    # User A accesses their own channel
    async def _override_user():
        return user_a

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/channels/{channel_a.id}")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Should return 200 with channel data
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(channel_a.id)
    assert payload["username"] == "user_a_own_channel"
    assert payload["title"] == f"Test Channel user_a_own_channel"


@pytest.mark.asyncio
async def test_get_channel_nonexistent():
    """Test that accessing a non-existent channel returns 404."""
    await init_db()

    # Create user
    user = await _create_user("user_nonexistent@example.com", "password123")

    # Try to access non-existent channel
    fake_channel_id = uuid4()

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/channels/{fake_channel_id}")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Should return 404
    assert response.status_code == 404
    assert response.json()["detail"] == "Channel not found"


# Test get_message endpoint


@pytest.mark.asyncio
async def test_get_message_unauthorized_access():
    """Test that user A cannot access user B's message."""
    await init_db()

    # Create user A with a channel and message
    user_a = await _create_user("user_a_message@example.com", "password123")
    channel_a = await _create_channel_for_user(user_a.id, "user_a_msg_channel")
    message_a = await _create_message_for_channel(channel_a.id, "User A's message")

    # Create user B
    user_b = await _create_user("user_b_message@example.com", "password123")

    # User B tries to access user A's message
    async def _override_user():
        return user_b

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/messages/{message_a.id}")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Should return 404 (not 403) to avoid information leakage
    assert response.status_code == 404
    assert response.json()["detail"] == "Message not found"


@pytest.mark.asyncio
async def test_get_message_authorized_access():
    """Test that user A can access their own message."""
    await init_db()

    # Create user A with a channel and message
    user_a = await _create_user("user_a_own_msg@example.com", "password123")
    channel_a = await _create_channel_for_user(user_a.id, "user_a_own_msg_ch")
    message_a = await _create_message_for_channel(channel_a.id, "User A's own message")

    # User A accesses their own message
    async def _override_user():
        return user_a

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/messages/{message_a.id}")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Should return 200 with message data
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(message_a.id)
    assert payload["original_text"] == "User A's own message"


@pytest.mark.asyncio
async def test_get_message_nonexistent():
    """Test that accessing a non-existent message returns 404."""
    await init_db()

    # Create user
    user = await _create_user("user_msg_nonexist@example.com", "password123")

    # Try to access non-existent message
    fake_message_id = uuid4()

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/messages/{fake_message_id}")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Should return 404
    assert response.status_code == 404
    assert response.json()["detail"] == "Message not found"


# Test delete_channel endpoint


@pytest.mark.asyncio
async def test_delete_channel_unauthorized_access():
    """Test that user A cannot delete user B's channel."""
    await init_db()

    # Create user A with a channel
    user_a = await _create_user("user_a_delete@example.com", "password123")
    channel_a = await _create_channel_for_user(user_a.id, "user_a_del_channel")

    # Create user B
    user_b = await _create_user("user_b_delete@example.com", "password123")

    # User B tries to delete user A's channel
    async def _override_user():
        return user_b

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/api/channels/{channel_a.id}")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Should return 404 (not 403) to avoid information leakage
    assert response.status_code == 404
    assert response.json()["detail"] == "Channel not found"

    # Verify that channel still exists for user A
    async def _override_user_a():
        return user_a

    app.dependency_overrides[current_active_user] = _override_user_a
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/channels/{channel_a.id}")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Channel should still be accessible for user A
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_channel_authorized_access():
    """Test that user A can delete their own channel."""
    await init_db()

    # Create user A with a channel
    user_a = await _create_user("user_a_del_own@example.com", "password123")
    channel_a = await _create_channel_for_user(user_a.id, "user_a_del_own_ch")

    # User A deletes their own channel
    async def _override_user():
        return user_a

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/api/channels/{channel_a.id}")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Should return 200
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_channel_no_enumeration():
    """Test that delete_channel doesn't leak channel existence information."""
    await init_db()

    # Create user A with a channel
    user_a = await _create_user("user_a_enum@example.com", "password123")
    channel_a = await _create_channel_for_user(user_a.id, "user_a_enum_ch")

    # Create user B
    user_b = await _create_user("user_b_enum@example.com", "password123")

    # User B tries to delete user A's existing channel
    async def _override_user():
        return user_b

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response_existing = await client.delete(f"/api/channels/{channel_a.id}")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # User B tries to delete a non-existent channel
    fake_channel_id = uuid4()

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response_nonexistent = await client.delete(f"/api/channels/{fake_channel_id}")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Both should return the same 404 error to prevent enumeration
    assert response_existing.status_code == 404
    assert response_nonexistent.status_code == 404
    assert response_existing.json()["detail"] == response_nonexistent.json()["detail"]
    assert response_existing.json()["detail"] == "Channel not found"


@pytest.mark.asyncio
async def test_shared_channel_access_isolation():
    """Test that two users can independently access a shared channel."""
    await init_db()

    # Create user A with a channel
    user_a = await _create_user("user_a_shared@example.com", "password123")
    channel = await _create_channel_for_user(user_a.id, "shared_channel")

    # Create user B and link them to the same channel
    user_b = await _create_user("user_b_shared@example.com", "password123")
    async with AsyncSessionLocal() as session:
        await session.execute(
            text(
                "INSERT INTO user_channels (id, user_id, channel_id, added_at) "
                "VALUES (:id, :user_id, :channel_id, :added_at)"
            ),
            {
                "id": str(uuid4()),
                "user_id": str(user_b.id),
                "channel_id": channel.id.hex,
                "added_at": None,
            },
        )
        await session.commit()

    # Both users should be able to access the channel
    async def _override_user_a():
        return user_a

    app.dependency_overrides[current_active_user] = _override_user_a
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response_a = await client.get(f"/api/channels/{channel.id}")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    async def _override_user_b():
        return user_b

    app.dependency_overrides[current_active_user] = _override_user_b
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response_b = await client.get(f"/api/channels/{channel.id}")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Both should successfully access the channel
    assert response_a.status_code == 200
    assert response_b.status_code == 200
    assert response_a.json()["id"] == str(channel.id)
    assert response_b.json()["id"] == str(channel.id)
