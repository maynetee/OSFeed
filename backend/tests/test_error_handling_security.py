"""
Security tests for error handling in API endpoints.

These tests verify that internal error details (database errors, stack traces,
exception messages) do not leak to API clients, while ensuring errors are
properly logged internally.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi_users.password import PasswordHelper
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from types import SimpleNamespace
from datetime import datetime, timezone
import base64

from app.main import app
from app.database import AsyncSessionLocal, init_db
from app.models.user import User
from app.models.channel import Channel
from app.auth.users import current_active_user
from sqlalchemy import text


async def _create_user(email: str, password: str) -> SimpleNamespace:
    """Helper to create a test user."""
    password_helper = PasswordHelper()
    user_id = str(uuid4())
    async with AsyncSessionLocal() as session:
        await session.execute(
            text(
                "INSERT INTO users (id, email, hashed_password, is_active, is_superuser, "
                "is_verified, role, data_retention_days, created_at) "
                "VALUES (:id, :email, :hashed_password, :is_active, :is_superuser, "
                ":is_verified, :role, :data_retention_days, :created_at)"
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
            },
        )
        await session.commit()
        return SimpleNamespace(id=user_id, email=email)


async def _create_channel_for_user(user_id: str, username: str) -> Channel:
    """Create a channel and link it to a user."""
    async with AsyncSessionLocal() as session:
        channel = Channel(
            username=username,
            telegram_id=12345,
            title="Test Channel",
            description="",
            subscriber_count=0,
            is_active=True,
        )
        session.add(channel)
        await session.flush()
        await session.execute(
            text(
                "INSERT INTO user_channels (id, user_id, channel_id, added_at) "
                "VALUES (:id, :user_id, :channel_id, :added_at)"
            ),
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "channel_id": channel.id.hex,
                "added_at": None,
            },
        )
        await session.commit()
        await session.refresh(channel)
        return channel


@pytest.mark.asyncio
async def test_channel_add_database_error_returns_generic_message(monkeypatch):
    """
    Test that database errors during channel addition return a generic error
    message without exposing database schema, SQL details, or internal paths.
    """
    await init_db()
    user = await _create_user("test_db_error@example.com", "password123")

    # Mock telegram client to succeed, so we reach the database save
    mock_client = AsyncMock()
    mock_client.resolve_channel.return_value = {
        "telegram_id": 99999,
        "title": "Test Channel",
        "description": "Test",
        "subscribers": 1000,
    }
    mock_client.join_public_channel.return_value = None
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    # Mock enqueue_fetch_job to raise a database-like error
    async def _raise_db_error(*args, **kwargs):
        raise Exception("psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint")

    monkeypatch.setattr("app.api.channels.enqueue_fetch_job", _raise_db_error)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels",
                json={"username": "testchannel"},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Verify generic error is returned
    assert response.status_code == 500
    error_detail = response.json()["detail"]

    # Should be generic error code/message
    assert error_detail == "CHANNEL_ADD_ERROR"

    # Should NOT contain internal details
    assert "psycopg2" not in error_detail.lower()
    assert "duplicate key" not in error_detail.lower()
    assert "constraint" not in error_detail.lower()
    assert "UniqueViolation" not in error_detail


@pytest.mark.asyncio
async def test_channel_add_value_error_returns_generic_message(monkeypatch):
    """
    Test that ValueError exceptions during channel resolution return a
    generic error message without exposing internal implementation details.
    """
    await init_db()
    user = await _create_user("test_value_error@example.com", "password123")

    # Mock telegram client to raise ValueError
    mock_client = AsyncMock()
    mock_client.resolve_channel.side_effect = ValueError("Internal telegram client error: invalid channel format @@@")
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels",
                json={"username": "invalidchannel"},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Verify generic error is returned
    assert response.status_code == 400
    error_detail = response.json()["detail"]

    # Should be generic message
    assert error_detail == "Unable to add channel. It may be private or invalid."

    # Should NOT contain ValueError details
    assert "ValueError" not in error_detail
    assert "telegram client error" not in error_detail.lower()
    assert "@@@" not in error_detail


@pytest.mark.asyncio
async def test_bulk_channel_add_error_returns_generic_message(monkeypatch):
    """
    Test that errors during bulk channel addition return generic messages
    in the failures list without exposing internal details.
    """
    await init_db()
    user = await _create_user("test_bulk_error@example.com", "password123")

    # Mock telegram client to raise an error for specific channel
    mock_client = AsyncMock()

    async def _resolve_with_error(username):
        if username == "badchannel":
            raise Exception("RuntimeError: /usr/lib/python3.11/telethon/errors.py line 42: Connection pool exhausted")
        return {
            "telegram_id": 99999,
            "title": "Good Channel",
            "description": "Test",
            "subscribers": 1000,
        }

    mock_client.resolve_channel.side_effect = _resolve_with_error
    mock_client.join_public_channel.return_value = None
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    # Mock enqueue to prevent actual job creation
    monkeypatch.setattr("app.api.channels.enqueue_fetch_job", AsyncMock(return_value=None))

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels/bulk",
                json={"usernames": ["goodchannel", "badchannel"]},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Verify response structure
    assert response.status_code == 200
    data = response.json()

    # Should have failures
    assert len(data["failures"]) > 0

    # Find the failure for badchannel
    bad_channel_failure = next((f for f in data["failures"] if f["username"] == "badchannel"), None)
    assert bad_channel_failure is not None

    # Should NOT contain internal paths or error details
    failure_message = bad_channel_failure["error"]
    assert "/usr/lib" not in failure_message
    assert "telethon/errors.py" not in failure_message
    assert "line 42" not in failure_message
    assert "RuntimeError" not in failure_message
    assert "Connection pool" not in failure_message


@pytest.mark.asyncio
async def test_invalid_cursor_format_returns_generic_message():
    """
    Test that invalid cursor format errors don't expose internal decoding
    details like base64 errors or parsing exceptions.
    """
    await init_db()
    user = await _create_user("test_cursor@example.com", "password123")

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Send malformed cursor
            response = await client.get(
                "/api/messages",
                params={"cursor": "this-is-not-valid-base64!@#$"},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Verify generic error is returned
    assert response.status_code == 400
    error_detail = response.json()["detail"]

    # Should be generic message
    assert error_detail == "Invalid cursor format"

    # Should NOT contain base64 decoding errors or exception details
    assert "base64" not in error_detail.lower()
    assert "binascii" not in error_detail.lower()
    assert "Incorrect padding" not in error_detail
    assert "ValueError" not in error_detail
    assert "Exception" not in error_detail


@pytest.mark.asyncio
async def test_malformed_cursor_data_returns_generic_message():
    """
    Test that cursors with valid base64 but invalid content structure
    return generic error without exposing parsing logic.
    """
    await init_db()
    user = await _create_user("test_cursor_data@example.com", "password123")

    # Create valid base64 but invalid cursor content (missing pipe separator)
    invalid_cursor = base64.urlsafe_b64encode(b"not-a-valid-cursor-format").decode("utf-8")

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/messages",
                params={"cursor": invalid_cursor},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Verify generic error
    assert response.status_code == 400
    error_detail = response.json()["detail"]

    assert error_detail == "Invalid cursor format"

    # Should NOT expose split/parsing errors
    assert "split" not in error_detail.lower()
    assert "not enough values to unpack" not in error_detail.lower()
    assert "list index" not in error_detail.lower()


@pytest.mark.asyncio
async def test_errors_are_logged_internally(monkeypatch):
    """
    Test that while errors return generic messages to clients, they are
    still logged internally with full details for debugging.
    """
    await init_db()
    user = await _create_user("test_logging@example.com", "password123")

    # Mock telegram client to raise an error
    mock_client = AsyncMock()
    test_error = Exception("Detailed internal error: database connection failed at host db.internal.example.com:5432")
    mock_client.resolve_channel.side_effect = test_error
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    # Mock the logger to capture log calls
    mock_logger = MagicMock()
    monkeypatch.setattr("app.api.channels.logger", mock_logger)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels",
                json={"username": "testchannel"},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Verify generic error to client
    assert response.status_code == 400
    assert response.json()["detail"] == "Unable to add channel. It may be private or invalid."

    # Verify detailed error was logged internally
    assert mock_logger.warning.called or mock_logger.error.called

    # Check that the log contains internal details
    log_calls = mock_logger.warning.call_args_list + mock_logger.error.call_args_list
    logged_messages = [str(call) for call in log_calls]
    logged_text = " ".join(logged_messages)

    # The internal error details should be in the logs
    assert "testchannel" in logged_text.lower() or any("testchannel" in str(call[0]) for call in log_calls)


@pytest.mark.asyncio
async def test_channel_refresh_error_returns_generic_message(monkeypatch):
    """
    Test that errors during channel refresh return generic messages
    without exposing telegram API or internal service errors.
    """
    await init_db()
    user = await _create_user("test_refresh@example.com", "password123")
    channel = await _create_channel_for_user(user.id, "refreshchannel")

    # Mock telegram client to raise error during refresh
    mock_client = AsyncMock()
    mock_client.fetch_channel_info.side_effect = Exception(
        "telethon.errors.rpcerrorlist.ChannelPrivateError: The channel specified is private (caused by GetFullChannelRequest)"
    )
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/channels/{channel.id}/refresh",
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Channel refresh may return various status codes, but should not expose error details
    error_data = response.json()

    # Verify no telethon-specific errors are exposed
    response_text = str(error_data)
    assert "telethon" not in response_text.lower()
    assert "rpcerrorlist" not in response_text.lower()
    assert "ChannelPrivateError" not in response_text
    assert "GetFullChannelRequest" not in response_text
    assert "caused by" not in response_text.lower()


@pytest.mark.asyncio
async def test_no_stack_traces_in_error_responses(monkeypatch):
    """
    Test that Python stack traces are never exposed in error responses,
    even for unexpected errors.
    """
    await init_db()
    user = await _create_user("test_stacktrace@example.com", "password123")

    # Mock telegram client to raise error with stack trace-like content
    mock_client = AsyncMock()
    mock_client.resolve_channel.side_effect = Exception(
        'Traceback (most recent call last):\n'
        '  File "/app/services/telegram.py", line 123, in connect\n'
        '    await self.client.connect()\n'
        'ConnectionError: [Errno 111] Connection refused'
    )
    monkeypatch.setattr("app.api.channels.get_telegram_client", lambda: mock_client)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels",
                json={"username": "testchannel"},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Verify generic error
    error_detail = response.json()["detail"]

    # Should NOT contain stack trace elements
    assert "Traceback" not in error_detail
    assert "File \"" not in error_detail
    assert "/app/services" not in error_detail
    assert "line 123" not in error_detail
    assert "ConnectionError" not in error_detail
    assert "[Errno" not in error_detail


@pytest.mark.asyncio
async def test_collection_create_database_error_returns_generic_message(monkeypatch):
    """
    Test that database errors during collection creation return generic
    error messages without exposing database schema or SQL details.
    """
    await init_db()
    user = await _create_user("test_collection_error@example.com", "password123")

    # Mock database session to raise a database error
    original_session = AsyncSessionLocal

    class MockSession:
        async def __aenter__(self):
            raise Exception("sqlalchemy.exc.IntegrityError: (psycopg2.errors.NotNullViolation) null value in column 'name' violates not-null constraint")

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("app.api.collections.AsyncSessionLocal", MockSession)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/collections",
                json={"name": "Test Collection", "channel_ids": []},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)
        monkeypatch.setattr("app.api.collections.AsyncSessionLocal", original_session)

    # Should return error without exposing database details
    assert response.status_code in [500, 400]
    error_detail = str(response.json().get("detail", ""))

    # Should NOT contain database error details
    assert "sqlalchemy" not in error_detail.lower()
    assert "psycopg2" not in error_detail.lower()
    assert "IntegrityError" not in error_detail
    assert "NotNullViolation" not in error_detail
    assert "not-null constraint" not in error_detail.lower()


@pytest.mark.asyncio
async def test_alert_create_database_error_returns_generic_message(monkeypatch):
    """
    Test that database errors during alert creation return generic
    error messages without exposing internal implementation details.
    """
    await init_db()
    user = await _create_user("test_alert_error@example.com", "password123")

    # Create a collection first (alerts require a collection)
    channel = await _create_channel_for_user(user.id, "alertchannel")

    async with AsyncSessionLocal() as session:
        from app.models.collection import Collection
        collection = Collection(
            name="Alert Test Collection",
            user_id=user.id,
        )
        session.add(collection)
        await session.commit()
        await session.refresh(collection)
        collection_id = collection.id

    # Mock database to raise error during alert creation
    from app.api import alerts
    original_create_alert = alerts.create_alert

    async def _mock_create_alert(*args, **kwargs):
        raise Exception("database.errors.ForeignKeyViolation: insert or update on table 'alerts' violates foreign key constraint 'fk_alerts_collection'")

    monkeypatch.setattr("app.api.alerts.create_alert", _mock_create_alert)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/alerts",
                json={
                    "collection_id": str(collection_id),
                    "trigger_type": "keyword",
                    "trigger_value": "test",
                },
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)
        monkeypatch.setattr("app.api.alerts.create_alert", original_create_alert)

    # Should return error without database details
    assert response.status_code in [500, 400, 404]
    error_detail = str(response.json().get("detail", ""))

    # Should NOT contain database constraint details
    assert "ForeignKeyViolation" not in error_detail
    assert "foreign key constraint" not in error_detail.lower()
    assert "fk_alerts_collection" not in error_detail
    assert "database.errors" not in error_detail.lower()


@pytest.mark.asyncio
async def test_auth_registration_unexpected_error_returns_generic_code(monkeypatch):
    """
    Test that unexpected errors during registration return a generic error
    code without exposing internal exception details.
    """
    await init_db()

    # Mock user manager to raise unexpected error
    from app.auth import users as auth_users
    original_user_manager_dependency = auth_users.get_user_manager

    async def _mock_user_manager():
        mock_manager = AsyncMock()
        mock_manager.create.side_effect = Exception(
            "Internal service error: redis connection to cache.internal.example.com:6379 failed with timeout after 5000ms"
        )
        return mock_manager

    monkeypatch.setattr("app.api.auth.get_user_manager", _mock_user_manager)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={"email": "test_unexpected@example.com", "password": "Str0ngP@ssword!"},
        )

    monkeypatch.setattr("app.api.auth.get_user_manager", original_user_manager_dependency)

    # Should return generic error code
    assert response.status_code == 500
    error_detail = response.json()["detail"]

    # Should be generic error code
    assert error_detail == "REGISTER_UNEXPECTED_ERROR"

    # Should NOT contain internal service details
    assert "redis" not in error_detail.lower()
    assert "cache.internal" not in error_detail.lower()
    assert "6379" not in error_detail
    assert "timeout" not in error_detail.lower()
    assert "5000ms" not in error_detail


@pytest.mark.asyncio
async def test_message_search_database_error_returns_generic_message(monkeypatch):
    """
    Test that database errors during message search return generic
    error messages without exposing query details or database internals.
    """
    await init_db()
    user = await _create_user("test_search_error@example.com", "password123")

    # Mock database session to raise error during search
    from app.api import messages
    original_session = messages.AsyncSessionLocal

    class MockSessionForSearch:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def execute(self, *args, **kwargs):
            raise Exception(
                "psycopg2.errors.QueryCanceled: canceling statement due to statement timeout\n"
                "CONTEXT: SQL statement \"SELECT messages.id, messages.telegram_id, messages.channel_id FROM messages WHERE to_tsvector('english', messages.text) @@ to_tsquery('english', $1)\""
            )

    monkeypatch.setattr("app.api.messages.AsyncSessionLocal", MockSessionForSearch)

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/messages/search",
                params={"query": "test"},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)
        monkeypatch.setattr("app.api.messages.AsyncSessionLocal", original_session)

    # Should return error without query details
    assert response.status_code in [500, 400]
    error_detail = str(response.json().get("detail", ""))

    # Should NOT contain SQL query or database internals
    assert "SELECT messages" not in error_detail
    assert "to_tsvector" not in error_detail
    assert "to_tsquery" not in error_detail
    assert "QueryCanceled" not in error_detail
    assert "statement timeout" not in error_detail.lower()
    assert "CONTEXT:" not in error_detail
    assert "psycopg2" not in error_detail.lower()


@pytest.mark.asyncio
async def test_export_format_error_returns_generic_message():
    """
    Test that export format validation returns user-friendly error
    messages without exposing internal format handling logic.
    """
    await init_db()
    user = await _create_user("test_export@example.com", "password123")
    channel = await _create_channel_for_user(user.id, "exportchannel")

    async with AsyncSessionLocal() as session:
        from app.models.collection import Collection
        collection = Collection(
            name="Export Test Collection",
            user_id=user.id,
        )
        session.add(collection)
        await session.commit()
        await session.refresh(collection)
        collection_id = collection.id

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Try invalid export format
            response = await client.get(
                f"/api/collections/{collection_id}/export",
                params={"format": "invalid_format_xyz"},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    # Should return clear error about format
    assert response.status_code == 400
    error_detail = response.json()["detail"]

    # Should be user-friendly generic message
    assert "Unsupported export format" in error_detail or "Invalid" in error_detail

    # Should NOT expose internal implementation
    assert "KeyError" not in error_detail
    assert "dict" not in error_detail.lower()
    assert "format_xyz" not in error_detail or "invalid" in error_detail.lower()
