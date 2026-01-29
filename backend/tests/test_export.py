import csv
import io
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi_users.password import PasswordHelper
from sqlalchemy import text

from app.main import app
from app.database import AsyncSessionLocal, init_db
from app.models.channel import Channel, user_channels
from app.models.collection import Collection, collection_channels
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
async def test_export_collection_csv() -> None:
    await init_db()
    user = await _create_user("export_csv@example.com", "password123")
    
    channel_id = uuid.uuid4()
    collection_id = uuid.uuid4()
    message_id = uuid.uuid4()
    
    async with AsyncSessionLocal() as session:
        # Create Channel
        channel = Channel(
            id=channel_id,
            username="export_channel",
            title="Export Channel",
            is_active=True
        )
        session.add(channel)
        await session.flush()
        
        # Link User-Channel (needed for permission checks often, though export uses collection ownership)
        await session.execute(
            text("INSERT INTO user_channels (id, user_id, channel_id) VALUES (:id, :uid, :cid)"),
            {"id": uuid.uuid4().hex, "uid": str(user.id), "cid": channel_id.hex}
        )
        
        # Create Message
        msg = Message(
            id=message_id,
            channel_id=channel_id,
            telegram_message_id=123,
            original_text="Hello Export World",
            published_at=datetime.now(timezone.utc),
            fetched_at=datetime.now(timezone.utc)
        )
        session.add(msg)
        
        # Create Collection
        collection = Collection(
            id=collection_id,
            user_id=user.id, # GUID expects UUID object or string? Model expects GUID type.
            # If inserting via ORM, pass UUID object.
            # But wait, we fixed the model to GUID.
            # Let's try ORM insert for Collection to verify it works with GUID fix.
            name="My Export Collection"
        )
        session.add(collection)
        await session.flush()
        
        # Link Collection-Channel
        await session.execute(
            text("INSERT INTO collection_channels (collection_id, channel_id) VALUES (:col_id, :chan_id)"),
            {"col_id": collection_id.hex, "chan_id": channel_id.hex} # UUID type expects 32-char hex in SQLite
        )
        await session.commit()

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/collections/{collection_id}/export?format=csv",
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    
    content = response.text
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    
    # Verify Metadata
    assert rows[0] == ["collection", "My Export Collection"]
    
    # Verify Header
    assert "original_text" in rows[4]
    
    # Verify Data
    found_msg = False
    for row in rows[5:]:
        if "Hello Export World" in row:
            found_msg = True
            break
    assert found_msg, "Message text not found in CSV"


@pytest.mark.asyncio
async def test_export_collection_html() -> None:
    await init_db()
    user = await _create_user("export_html@example.com", "password123")
    
    channel_id = uuid.uuid4()
    collection_id = uuid.uuid4()
    
    async with AsyncSessionLocal() as session:
        channel = Channel(id=channel_id, username="html_channel", title="HTML Channel")
        session.add(channel)
        
        msg = Message(
            channel_id=channel_id,
            telegram_message_id=456,
            original_text="<b>Bold Text</b>",
            published_at=datetime.now(timezone.utc),
            fetched_at=datetime.now(timezone.utc)
        )
        session.add(msg)
        
        collection = Collection(id=collection_id, user_id=user.id, name="HTML Collection")
        session.add(collection)
        await session.flush()
        
        await session.execute(
            text("INSERT INTO collection_channels (collection_id, channel_id) VALUES (:col_id, :chan_id)"),
            {"col_id": collection_id.hex, "chan_id": channel_id.hex}
        )
        await session.commit()

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/collections/{collection_id}/export?format=html",
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "HTML Collection" in response.text
    assert "&lt;b&gt;Bold Text&lt;/b&gt;" in response.text or "<b>Bold Text</b>" in response.text
