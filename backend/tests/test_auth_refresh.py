import pytest
from httpx import AsyncClient, ASGITransport

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

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_response = await client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "password123"},
        )
        assert login_response.status_code == 200

        # Verify tokens are in cookies, not JSON body
        assert "access_token" in login_response.cookies
        assert "refresh_token" in login_response.cookies

        # Verify JSON response contains user info only
        payload = login_response.json()
        assert "user" in payload
        assert payload["user"]["email"] == "test@example.com"
        assert "access_token" not in payload
        assert "refresh_token" not in payload

        # Verify cookie attributes
        access_cookie = login_response.cookies.get("access_token")
        refresh_cookie = login_response.cookies.get("refresh_token")
        assert access_cookie is not None
        assert refresh_cookie is not None

        # Refresh using cookies (cookies are automatically sent by the client)
        refresh_response = await client.post("/api/auth/refresh")
        assert refresh_response.status_code == 200

        # Verify new tokens are in cookies
        assert "access_token" in refresh_response.cookies
        assert "refresh_token" in refresh_response.cookies

        # Verify JSON response contains user info only
        refresh_payload = refresh_response.json()
        assert "user" in refresh_payload
        assert "access_token" not in refresh_payload
        assert "refresh_token" not in refresh_payload


@pytest.mark.asyncio
async def test_refresh_token_rejects_invalid_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Set invalid refresh token cookie
        response = await client.post(
            "/api/auth/refresh",
            cookies={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401
