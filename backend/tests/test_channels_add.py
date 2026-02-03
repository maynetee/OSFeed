import itertools
from uuid import UUID, uuid4
from types import SimpleNamespace
from typing import Optional
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi_users.password import PasswordHelper

from app.main import app
from app.database import AsyncSessionLocal, init_db
from app.models.channel import Channel, user_channels
from app.models.fetch_job import FetchJob
from app.auth.users import current_active_user
from sqlalchemy import text, select
from datetime import datetime, timezone

_telegram_id_counter = itertools.count(100000)


async def _create_user(email: str, password: str) -> SimpleNamespace:
    password_helper = PasswordHelper()
    user_id = str(uuid4())
    async with AsyncSessionLocal() as session:
        await session.execute(
            text(
                "INSERT INTO users (id, email, hashed_password, is_active, is_superuser, "
                "is_verified, role, data_retention_days, preferred_language, created_at) "
                "VALUES (:id, :email, :hashed_password, :is_active, :is_superuser, "
                ":is_verified, :role, :data_retention_days, :preferred_language, :created_at)"
            ),
            {
                "id": user_id,
                "email": email,
                "hashed_password": password_helper.hash(password),
                "is_active": True,
                "is_superuser": False,
                "is_verified": True,
                "role": "viewer",
                "data_retention_days": 365,
                "preferred_language": "en",
                "created_at": datetime.now(timezone.utc),
            },
        )
        await session.commit()
        return SimpleNamespace(id=UUID(user_id), email=email)


async def _create_channel(username: str, telegram_id: Optional[int] = None) -> Channel:
    """Create a channel without linking to any user."""
    if telegram_id is None:
        telegram_id = next(_telegram_id_counter)
    async with AsyncSessionLocal() as session:
        channel = Channel(
            username=username,
            telegram_id=telegram_id,
            title=f"Test Channel {username}",
            description="Test description",
            subscriber_count=1000,
            is_active=True,
        )
        session.add(channel)
        await session.commit()
        await session.refresh(channel)
        return channel


async def _create_channel_for_user(user_id, username: str) -> Channel:
    """Create a channel and link it to a user."""
    async with AsyncSessionLocal() as session:
        channel = Channel(
            username=username,
            telegram_id=next(_telegram_id_counter),
            title="Test Channel",
            description="",
            subscriber_count=0,
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


def _mock_telegram_client():
    """Create a mock telegram client for testing."""
    mock_client = AsyncMock()
    mock_client.can_join_channel.return_value = True

    async def _resolve_channel(username):
        return {
            "telegram_id": next(_telegram_id_counter),
            "title": "Mocked Channel Title",
            "description": "Mocked description",
            "subscribers": 5000,
        }

    mock_client.resolve_channel = AsyncMock(side_effect=_resolve_channel)
    mock_client.join_public_channel.return_value = None
    mock_client.record_channel_join.return_value = None
    return mock_client


@pytest.mark.asyncio
async def test_add_channel_success(monkeypatch):
    """Test successfully adding a new channel."""
    await init_db()
    user = await _create_user("add_single@example.com", "password123")

    mock_client = _mock_telegram_client()
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    job_id = uuid4()
    mock_job = FetchJob(
        id=job_id,
        channel_id=uuid4(),
        days=7,
        status="queued",
        stage="queued",
        created_at=datetime.now(timezone.utc),
    )
    mock_enqueue = AsyncMock(return_value=mock_job)
    monkeypatch.setattr("app.api.channels.enqueue_fetch_job", mock_enqueue)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels",
                json={"username": "testchannel1"},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "testchannel1"
    assert payload["title"] == "Mocked Channel Title"
    assert payload["is_active"] is True
    mock_client.resolve_channel.assert_awaited_once_with("testchannel1")
    mock_client.join_public_channel.assert_awaited_once_with("testchannel1")


@pytest.mark.asyncio
async def test_add_channel_with_url_prefix(monkeypatch):
    """Test adding a channel with https://t.me/ prefix."""
    await init_db()
    user = await _create_user("add_url@example.com", "password123")

    mock_client = _mock_telegram_client()
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    mock_enqueue = AsyncMock(return_value=None)
    monkeypatch.setattr("app.api.channels.enqueue_fetch_job", mock_enqueue)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels",
                json={"username": "https://t.me/urlchannel"},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "urlchannel"


@pytest.mark.asyncio
async def test_add_channel_with_at_symbol(monkeypatch):
    """Test adding a channel with @ prefix."""
    await init_db()
    user = await _create_user("add_at@example.com", "password123")

    mock_client = _mock_telegram_client()
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    mock_enqueue = AsyncMock(return_value=None)
    monkeypatch.setattr("app.api.channels.enqueue_fetch_job", mock_enqueue)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels",
                json={"username": "@atchannel"},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "atchannel"


@pytest.mark.asyncio
async def test_add_channel_invalid_username_format():
    """Test adding a channel with invalid username format."""
    await init_db()
    user = await _create_user("invalid_format@example.com", "password123")

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Too short
            response = await client.post(
                "/api/channels",
                json={"username": "ab"},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 400
    assert "Invalid Telegram username format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_add_channel_already_exists_in_list(monkeypatch):
    """Test adding a channel that already exists in user's list."""
    await init_db()
    user = await _create_user("already_exists@example.com", "password123")
    await _create_channel_for_user(user.id, "existingchannel")

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels",
                json={"username": "existingchannel"},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 400
    assert "already exists in your list" in response.json()["detail"]


@pytest.mark.asyncio
async def test_add_channel_links_existing_channel(monkeypatch):
    """Test adding a channel that exists (from another user) creates a link."""
    await init_db()

    # Create first user with a channel
    user1 = await _create_user("user1_link@example.com", "password123")
    channel = await _create_channel_for_user(user1.id, "sharedchannel")

    # Create second user
    user2 = await _create_user("user2_link@example.com", "password123")

    mock_client = _mock_telegram_client()
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    mock_enqueue = AsyncMock(return_value=None)
    monkeypatch.setattr("app.api.channels.enqueue_fetch_job", mock_enqueue)

    async def _override_user():
        return user2

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels",
                json={"username": "sharedchannel"},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "sharedchannel"
    # The channel should be the same one (linked, not new)
    assert payload["id"] == str(channel.id)


@pytest.mark.asyncio
async def test_add_channel_telegram_error(monkeypatch):
    """Test adding a channel when Telegram returns an error."""
    await init_db()
    user = await _create_user("telegram_error@example.com", "password123")

    mock_client = _mock_telegram_client()
    mock_client.resolve_channel.side_effect = ValueError("Channel not found or is private")
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels",
                json={"username": "privatechannel"},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 400
    assert response.json()["detail"] == "Unable to add channel. It may be private or invalid."


# Bulk channel addition tests

@pytest.mark.asyncio
async def test_bulk_add_channels_success(monkeypatch):
    """Test successfully adding multiple channels in bulk."""
    await init_db()
    user = await _create_user("bulk_success@example.com", "password123")

    mock_client = _mock_telegram_client()
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    mock_enqueue = AsyncMock(return_value=None)
    monkeypatch.setattr("app.api.channels.enqueue_fetch_job", mock_enqueue)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels/bulk",
                json={"usernames": ["bulkchannel1", "bulkchannel2", "bulkchannel3"]},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["success_count"] == 3
    assert payload["failure_count"] == 0
    assert len(payload["succeeded"]) == 3
    assert len(payload["failed"]) == 0


@pytest.mark.asyncio
async def test_bulk_add_channels_partial_success(monkeypatch):
    """Test bulk adding channels where some succeed and some fail."""
    await init_db()
    user = await _create_user("bulk_partial@example.com", "password123")

    # Create a channel that already exists for this user
    await _create_channel_for_user(user.id, "alreadyexists")

    mock_client = _mock_telegram_client()
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    mock_enqueue = AsyncMock(return_value=None)
    monkeypatch.setattr("app.api.channels.enqueue_fetch_job", mock_enqueue)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels/bulk",
                json={"usernames": ["newchannel1", "alreadyexists", "newchannel2"]},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["success_count"] == 2
    assert payload["failure_count"] == 1
    assert len(payload["succeeded"]) == 2
    assert len(payload["failed"]) == 1
    assert payload["failed"][0]["username"] == "alreadyexists"
    assert "already exists" in payload["failed"][0]["error"]


@pytest.mark.asyncio
async def test_bulk_add_channels_empty_list():
    """Test bulk adding with empty usernames list."""
    await init_db()
    user = await _create_user("bulk_empty@example.com", "password123")

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels/bulk",
                json={"usernames": []},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 0
    assert payload["success_count"] == 0
    assert payload["failure_count"] == 0


@pytest.mark.asyncio
async def test_bulk_add_channels_invalid_format(monkeypatch):
    """Test bulk adding with invalid username formats."""
    await init_db()
    user = await _create_user("bulk_invalid@example.com", "password123")

    mock_client = _mock_telegram_client()
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    mock_enqueue = AsyncMock(return_value=None)
    monkeypatch.setattr("app.api.channels.enqueue_fetch_job", mock_enqueue)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels/bulk",
                json={"usernames": ["validchannel1", "ab", "1invalid", "validchannel2"]},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 4
    assert payload["success_count"] == 2
    assert payload["failure_count"] == 2

    # Check that valid channels succeeded
    succeeded_usernames = [c["username"] for c in payload["succeeded"]]
    assert "validchannel1" in succeeded_usernames
    assert "validchannel2" in succeeded_usernames

    # Check that invalid channels failed with proper error
    failed_usernames = [f["username"] for f in payload["failed"]]
    assert "ab" in failed_usernames
    assert "1invalid" in failed_usernames


@pytest.mark.asyncio
async def test_bulk_add_channels_with_url_prefixes(monkeypatch):
    """Test bulk adding channels with various URL formats."""
    await init_db()
    user = await _create_user("bulk_urls@example.com", "password123")

    mock_client = _mock_telegram_client()
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    mock_enqueue = AsyncMock(return_value=None)
    monkeypatch.setattr("app.api.channels.enqueue_fetch_job", mock_enqueue)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels/bulk",
                json={"usernames": [
                    "https://t.me/urlchan1",
                    "t.me/urlchan2",
                    "@urlchan3",
                    "urlchan4"
                ]},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 4
    assert payload["success_count"] == 4

    # Check that usernames were properly cleaned
    succeeded_usernames = [c["username"] for c in payload["succeeded"]]
    assert "urlchan1" in succeeded_usernames
    assert "urlchan2" in succeeded_usernames
    assert "urlchan3" in succeeded_usernames
    assert "urlchan4" in succeeded_usernames


@pytest.mark.asyncio
async def test_bulk_add_channels_telegram_error(monkeypatch):
    """Test bulk adding when Telegram errors for some channels."""
    await init_db()
    user = await _create_user("bulk_tg_error@example.com", "password123")

    mock_client = _mock_telegram_client()

    # Make resolve_channel fail for specific channels
    async def conditional_resolve(username):
        if username == "privatechan":
            raise ValueError("Channel is private")
        return {
            "telegram_id": next(_telegram_id_counter),
            "title": f"Channel {username}",
            "description": "Description",
            "subscribers": 1000,
        }

    mock_client.resolve_channel = conditional_resolve
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    mock_enqueue = AsyncMock(return_value=None)
    monkeypatch.setattr("app.api.channels.enqueue_fetch_job", mock_enqueue)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels/bulk",
                json={"usernames": ["publicchan", "privatechan", "anotherchan"]},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["success_count"] == 2
    assert payload["failure_count"] == 1

    # Check that the private channel failed
    assert len(payload["failed"]) == 1
    assert payload["failed"][0]["username"] == "privatechan"
    assert "private" in payload["failed"][0]["error"]


@pytest.mark.asyncio
async def test_add_channel_join_limit_reached(monkeypatch):
    """Test adding a channel when daily join limit is reached."""
    await init_db()
    user = await _create_user("join_limit@example.com", "password123")

    mock_client = _mock_telegram_client()
    mock_client.can_join_channel.return_value = False
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    # Disable queue so we get immediate 429 error
    monkeypatch.setattr("app.api.channels.settings.telegram_join_channel_queue_enabled", False)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels",
                json={"username": "limitchannel"},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 429
    assert "Daily channel join limit reached" in response.json()["detail"]
