import pytest
from httpx import AsyncClient

from fastapi_users.password import PasswordHelper

from app.main import app
from app.database import AsyncSessionLocal, init_db
from app.models.user import User


@pytest.mark.asyncio
async def test_login_and_refresh_token_flow():
    await init_db()
    password_helper = PasswordHelper()

    async with AsyncSessionLocal() as session:
        user = User(
            email="test@example.com",
            hashed_password=password_helper.hash("password123"),
            is_active=True,
            is_superuser=False,
            is_verified=True,
        )
        session.add(user)
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        login_response = await client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "password123"},
        )
        assert login_response.status_code == 200
        payload = login_response.json()
        assert "access_token" in payload
        assert "refresh_token" in payload

        refresh_response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": payload["refresh_token"]},
        )
        assert refresh_response.status_code == 200
        refresh_payload = refresh_response.json()
        assert refresh_payload["access_token"]
        assert refresh_payload["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_token_rejects_invalid_token():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401
