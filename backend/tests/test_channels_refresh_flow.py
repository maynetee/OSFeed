from uuid import UUID, uuid4
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi_users.password import PasswordHelper

from app.main import app
from app.database import AsyncSessionLocal, init_db
from app.models.channel import Channel, user_channels
from app.models.fetch_job import FetchJob
from app.auth.users import current_active_user
from sqlalchemy import text
from datetime import datetime, timezone


async def _create_user(email: str, password: str) -> SimpleNamespace:
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
        return SimpleNamespace(id=UUID(user_id), email=email)


async def _create_channel_for_user(user_id, username: str) -> Channel:
    async with AsyncSessionLocal() as session:
        channel = Channel(
            username=username,
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


@pytest.mark.asyncio
async def test_refresh_enqueues_jobs(monkeypatch):
    await init_db()
    user = await _create_user("refresh@example.com", "password123")
    channel = await _create_channel_for_user(user.id, "refresh_channel")

    job_id = uuid4()
    mock_job = FetchJob(
        id=job_id,
        channel_id=channel.id,
        days=7,
        status="queued",
        stage="queued",
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
                "/api/channels/refresh",
                json={"channel_ids": [str(channel.id)]},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_ids"] == [str(job_id)]
    mock_enqueue.assert_awaited()


@pytest.mark.asyncio
async def test_fetch_jobs_status_returns_jobs():
    await init_db()
    user = await _create_user("status@example.com", "password123")
    channel = await _create_channel_for_user(user.id, "status_channel")

    async with AsyncSessionLocal() as session:
        job = FetchJob(
            channel_id=channel.id,
            days=7,
            status="queued",
            stage="queued",
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        job_id = job.id

    async def _override_user():
        return user

    app.dependency_overrides[current_active_user] = _override_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/channels/fetch-jobs/status",
                json={"job_ids": [str(job_id)]},
            )
    finally:
        app.dependency_overrides.pop(current_active_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["jobs"]) == 1
    assert payload["jobs"][0]["id"] == str(job_id)
