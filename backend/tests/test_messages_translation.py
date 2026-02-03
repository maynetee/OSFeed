import json
import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi_users.password import PasswordHelper
from sqlalchemy import select

from app.main import app
from app.database import AsyncSessionLocal, init_db
from app.models.channel import Channel, user_channels
from app.models.message import Message
from app.models.user import User
from app.services.translator import translator


async def _create_user(email: str = "test-messages@example.com") -> None:
    password_helper = PasswordHelper()
    async with AsyncSessionLocal() as session:
        user = User(
            email=email,
            hashed_password=password_helper.hash("password123"),
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )
        session.add(user)
        await session.commit()


async def _login(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    # Tokens are now in httpOnly cookies, not JSON body
    access_token = response.cookies.get("access_token")
    assert access_token, "access_token cookie not set in login response"
    return access_token


@pytest.mark.asyncio
async def test_translate_message_on_demand_updates_message(monkeypatch) -> None:
    await init_db()

    email = f"messages-{uuid.uuid4()}@example.com"
    await _create_user(email)

    channel_id = uuid.uuid4()
    message_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        # Fetch user
        user = (await session.execute(select(User).where(User.email == email))).scalar_one()

        channel = Channel(
            id=channel_id,
            username="testchannel",
            title="Test Channel",
        )
        session.add(channel)
        await session.commit()

        # Manually link user to channel
        await session.execute(
            user_channels.insert().values(
                user_id=user.id,
                channel_id=channel.id
            )
        )

        session.add(
            Message(
                id=message_id,
                channel_id=channel_id,
                telegram_message_id=123,
                original_text="Hola mundo",
                translated_text=None,
                target_language="en",
                needs_translation=True,
                published_at=datetime.now(timezone.utc),
                fetched_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()

    async def _fake_translate(text: str, **kwargs):
        assert text == "Hola mundo"
        return "Hello world", "es", "normal"

    monkeypatch.setattr(translator, "translate", _fake_translate)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client, email, "password123")
        response = await client.post(
            f"/api/messages/{message_id}/translate",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["translated_text"] == "Hello world"
    assert payload["needs_translation"] is False

    async with AsyncSessionLocal() as session:
        refreshed = await session.get(Message, message_id)
        assert refreshed is not None
        assert refreshed.translated_text == "Hello world"
        assert refreshed.needs_translation is False


@pytest.mark.asyncio
async def test_stream_messages_batches() -> None:
    await init_db()

    email = f"stream-{uuid.uuid4()}@example.com"
    await _create_user(email)

    channel_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        # Fetch user
        user = (await session.execute(select(User).where(User.email == email))).scalar_one()

        channel = Channel(
            id=channel_id,
            username="streamchannel",
            title="Stream Channel",
        )
        session.add(channel)
        await session.commit()
        
        # Manually link user to channel
        await session.execute(
            user_channels.insert().values(
                user_id=user.id,
                channel_id=channel.id
            )
        )

        session.add_all(
            [
                Message(
                    channel_id=channel_id,
                    telegram_message_id=idx,
                    original_text=f"Message {idx}",
                    translated_text=None,
                    needs_translation=True,
                    published_at=datetime.now(timezone.utc),
                    fetched_at=datetime.now(timezone.utc),
                )
                for idx in range(1, 4)
            ]
        )
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login(client, email, "password123")
        async with client.stream(
            "GET",
            "/api/messages/stream?batch_size=2&limit=3",
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            body = (await response.aread()).decode("utf-8")

    assert response.status_code == 200
    data_lines = [line for line in body.splitlines() if line.startswith("data: ")]
    assert data_lines
    first_payload = json.loads(data_lines[0].split("data: ", 1)[1])
    assert first_payload["count"] == 2
    assert len(first_payload["messages"]) == 2
