import uuid
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi_users.password import PasswordHelper
from sqlalchemy import text

from app.main import app
from app.database import AsyncSessionLocal, init_db
from app.models.channel import Channel
from app.models.message import Message
from app.auth.users import current_active_user


async def _create_user(email: str, password: str) -> SimpleNamespace:
    password_helper = PasswordHelper()
    user_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        await session.execute(
            text(
                "INSERT INTO users (id, email, hashed_password, is_active, is_superuser, "
                "is_verified, role, data_retention_days, created_at, preferred_language) "
                "VALUES (:id, :email, :hashed_password, :is_active, :is_superuser, "
                ":is_verified, :role, :data_retention_days, :created_at, :preferred_language)"
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
                "created_at": datetime.now(timezone.utc),
                "preferred_language": "en",
            },
        )
        await session.commit()
        return SimpleNamespace(id=uuid.UUID(user_id), email=email)


@pytest.mark.asyncio
async def test_overview_stats_empty_database() -> None:
    """Test that empty database returns all zeros."""
    await init_db()
    user = await _create_user("empty_stats@example.com", "password123")

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/stats/overview")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    data = response.json()
    assert data["total_messages"] == 0
    assert data["active_channels"] == 0
    assert data["messages_last_24h"] == 0
    assert data["duplicates_last_24h"] == 0


@pytest.mark.asyncio
async def test_overview_stats_messages_older_than_24h() -> None:
    """Test that messages older than 24h are only counted in total_messages."""
    await init_db()
    user = await _create_user("old_messages@example.com", "password123")

    channel_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    two_days_ago = now - timedelta(days=2)

    async with AsyncSessionLocal() as session:
        # Create Channel
        channel = Channel(
            id=channel_id,
            username="test_channel",
            title="Test Channel",
            is_active=True
        )
        session.add(channel)
        await session.flush()

        # Link User-Channel
        await session.execute(
            text("INSERT INTO user_channels (id, user_id, channel_id) VALUES (:id, :uid, :cid)"),
            {"id": uuid.uuid4().hex, "uid": str(user.id), "cid": channel_id.hex}
        )

        # Create old message (2 days ago)
        msg = Message(
            channel_id=channel_id,
            telegram_message_id=123,
            original_text="Old message",
            published_at=two_days_ago,
            fetched_at=now,
            is_duplicate=False
        )
        session.add(msg)
        await session.commit()

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/stats/overview")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    data = response.json()
    assert data["total_messages"] == 1
    assert data["active_channels"] == 1
    assert data["messages_last_24h"] == 0
    assert data["duplicates_last_24h"] == 0


@pytest.mark.asyncio
async def test_overview_stats_duplicates_within_24h() -> None:
    """Test that duplicates within 24h are counted in both duplicates_24h and messages_24h."""
    await init_db()
    user = await _create_user("duplicates@example.com", "password123")

    channel_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)

    async with AsyncSessionLocal() as session:
        # Create Channel
        channel = Channel(
            id=channel_id,
            username="dup_channel",
            title="Duplicate Channel",
            is_active=True
        )
        session.add(channel)
        await session.flush()

        # Link User-Channel
        await session.execute(
            text("INSERT INTO user_channels (id, user_id, channel_id) VALUES (:id, :uid, :cid)"),
            {"id": uuid.uuid4().hex, "uid": str(user.id), "cid": channel_id.hex}
        )

        # Create duplicate message (1 hour ago)
        msg_dup = Message(
            channel_id=channel_id,
            telegram_message_id=456,
            original_text="Duplicate message",
            published_at=one_hour_ago,
            fetched_at=now,
            is_duplicate=True,
            originality_score=10
        )
        session.add(msg_dup)

        # Create non-duplicate message (1 hour ago)
        msg_orig = Message(
            channel_id=channel_id,
            telegram_message_id=789,
            original_text="Original message",
            published_at=one_hour_ago,
            fetched_at=now,
            is_duplicate=False,
            originality_score=100
        )
        session.add(msg_orig)
        await session.commit()

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/stats/overview")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    data = response.json()
    assert data["total_messages"] == 2
    assert data["active_channels"] == 1
    assert data["messages_last_24h"] == 2
    assert data["duplicates_last_24h"] == 1


@pytest.mark.asyncio
async def test_overview_stats_user_isolation() -> None:
    """Test that user A doesn't see user B's stats."""
    await init_db()
    user_a = await _create_user("usera@example.com", "password123")
    user_b = await _create_user("userb@example.com", "password123")

    channel_a_id = uuid.uuid4()
    channel_b_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as session:
        # Create Channel A (for user A)
        channel_a = Channel(
            id=channel_a_id,
            username="channel_a",
            title="Channel A",
            is_active=True
        )
        session.add(channel_a)

        # Create Channel B (for user B)
        channel_b = Channel(
            id=channel_b_id,
            username="channel_b",
            title="Channel B",
            is_active=True
        )
        session.add(channel_b)
        await session.flush()

        # Link User A to Channel A
        await session.execute(
            text("INSERT INTO user_channels (id, user_id, channel_id) VALUES (:id, :uid, :cid)"),
            {"id": uuid.uuid4().hex, "uid": str(user_a.id), "cid": channel_a_id.hex}
        )

        # Link User B to Channel B
        await session.execute(
            text("INSERT INTO user_channels (id, user_id, channel_id) VALUES (:id, :uid, :cid)"),
            {"id": uuid.uuid4().hex, "uid": str(user_b.id), "cid": channel_b_id.hex}
        )

        # Create message in Channel A
        msg_a = Message(
            channel_id=channel_a_id,
            telegram_message_id=111,
            original_text="Message A",
            published_at=now,
            fetched_at=now,
            is_duplicate=False
        )
        session.add(msg_a)

        # Create message in Channel B
        msg_b = Message(
            channel_id=channel_b_id,
            telegram_message_id=222,
            original_text="Message B",
            published_at=now,
            fetched_at=now,
            is_duplicate=False
        )
        session.add(msg_b)
        await session.commit()

    # Test User A sees only their data
    async def _override_user_a():
        return user_a

    app.dependency_overrides[current_active_user] = _override_user_a
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/stats/overview")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    data = response.json()
    assert data["total_messages"] == 1
    assert data["active_channels"] == 1
    assert data["messages_last_24h"] == 1
    assert data["duplicates_last_24h"] == 0

    # Test User B sees only their data
    async def _override_user_b():
        return user_b

    app.dependency_overrides[current_active_user] = _override_user_b
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/stats/overview")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    data = response.json()
    assert data["total_messages"] == 1
    assert data["active_channels"] == 1
    assert data["messages_last_24h"] == 1
    assert data["duplicates_last_24h"] == 0


@pytest.mark.asyncio
async def test_overview_stats_active_vs_inactive_channels() -> None:
    """Test that only active channels are counted."""
    await init_db()
    user = await _create_user("active_channels@example.com", "password123")

    channel_active_id = uuid.uuid4()
    channel_inactive_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as session:
        # Create Active Channel
        channel_active = Channel(
            id=channel_active_id,
            username="active_channel",
            title="Active Channel",
            is_active=True
        )
        session.add(channel_active)

        # Create Inactive Channel
        channel_inactive = Channel(
            id=channel_inactive_id,
            username="inactive_channel",
            title="Inactive Channel",
            is_active=False
        )
        session.add(channel_inactive)
        await session.flush()

        # Link User to both channels
        await session.execute(
            text("INSERT INTO user_channels (id, user_id, channel_id) VALUES (:id, :uid, :cid)"),
            {"id": uuid.uuid4().hex, "uid": str(user.id), "cid": channel_active_id.hex}
        )
        await session.execute(
            text("INSERT INTO user_channels (id, user_id, channel_id) VALUES (:id, :uid, :cid)"),
            {"id": uuid.uuid4().hex, "uid": str(user.id), "cid": channel_inactive_id.hex}
        )

        # Create message in active channel
        msg_active = Message(
            channel_id=channel_active_id,
            telegram_message_id=333,
            original_text="Active message",
            published_at=now,
            fetched_at=now,
            is_duplicate=False
        )
        session.add(msg_active)

        # Create message in inactive channel
        msg_inactive = Message(
            channel_id=channel_inactive_id,
            telegram_message_id=444,
            original_text="Inactive message",
            published_at=now,
            fetched_at=now,
            is_duplicate=False
        )
        session.add(msg_inactive)
        await session.commit()

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/stats/overview")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    data = response.json()
    # Messages from both active and inactive channels are counted
    assert data["total_messages"] == 2
    # Only active channels are counted
    assert data["active_channels"] == 1
    assert data["messages_last_24h"] == 2
    assert data["duplicates_last_24h"] == 0


@pytest.mark.asyncio
async def test_overview_stats_mixed_scenario() -> None:
    """Test comprehensive scenario with multiple messages, duplicates, and time periods."""
    await init_db()
    user = await _create_user("mixed@example.com", "password123")

    channel_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)
    three_days_ago = now - timedelta(days=3)

    async with AsyncSessionLocal() as session:
        # Create Channel
        channel = Channel(
            id=channel_id,
            username="mixed_channel",
            title="Mixed Channel",
            is_active=True
        )
        session.add(channel)
        await session.flush()

        # Link User-Channel
        await session.execute(
            text("INSERT INTO user_channels (id, user_id, channel_id) VALUES (:id, :uid, :cid)"),
            {"id": uuid.uuid4().hex, "uid": str(user.id), "cid": channel_id.hex}
        )

        # Old non-duplicate message (3 days ago)
        msg1 = Message(
            channel_id=channel_id,
            telegram_message_id=501,
            original_text="Old message 1",
            published_at=three_days_ago,
            fetched_at=now,
            is_duplicate=False
        )
        session.add(msg1)

        # Old duplicate message (3 days ago)
        msg2 = Message(
            channel_id=channel_id,
            telegram_message_id=502,
            original_text="Old duplicate",
            published_at=three_days_ago,
            fetched_at=now,
            is_duplicate=True
        )
        session.add(msg2)

        # Recent non-duplicate message (1 hour ago)
        msg3 = Message(
            channel_id=channel_id,
            telegram_message_id=503,
            original_text="Recent message",
            published_at=one_hour_ago,
            fetched_at=now,
            is_duplicate=False
        )
        session.add(msg3)

        # Recent duplicate message (1 hour ago)
        msg4 = Message(
            channel_id=channel_id,
            telegram_message_id=504,
            original_text="Recent duplicate",
            published_at=one_hour_ago,
            fetched_at=now,
            is_duplicate=True
        )
        session.add(msg4)

        # Another recent duplicate (1 hour ago)
        msg5 = Message(
            channel_id=channel_id,
            telegram_message_id=505,
            original_text="Another recent duplicate",
            published_at=one_hour_ago,
            fetched_at=now,
            is_duplicate=True
        )
        session.add(msg5)

        await session.commit()

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/stats/overview")
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    data = response.json()
    # All messages counted in total
    assert data["total_messages"] == 5
    assert data["active_channels"] == 1
    # Only recent messages (1 hour ago) counted: 3 messages
    assert data["messages_last_24h"] == 3
    # Only recent duplicates (1 hour ago) counted: 2 duplicates
    assert data["duplicates_last_24h"] == 2
