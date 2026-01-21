import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from fastapi_users.password import PasswordHelper

from app.main import app
from app.database import AsyncSessionLocal, init_db
from app.models.user import User


@pytest.mark.asyncio
async def test_logout_endpoint():
    await init_db()
    password_helper = PasswordHelper()
    
    # Create test user
    async with AsyncSessionLocal() as session:
        # Check if user exists to avoid unique constraint error if tests are re-run on same DB
        result = await session.execute(select(User).where(User.email == "test_logout@example.com"))
        existing_user = result.scalars().first()
        
        if not existing_user:
            user = User(
                email="test_logout@example.com",
                hashed_password=password_helper.hash("password123"),
                is_active=True,
                is_superuser=False,
                is_verified=True,
            )
            session.add(user)
            await session.commit()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login
        login_response = await client.post(
            "/api/auth/login",
            data={"username": "test_logout@example.com", "password": "password123"},
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        access_token = tokens["access_token"]
        
        # Verify user has refresh token hash
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == "test_logout@example.com"))
            user = result.scalars().first()
            assert user.refresh_token_hash is not None
        
        # Logout
        logout_response = await client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert logout_response.status_code == 200
        assert logout_response.json()["message"] == "Successfully logged out"
        
        # Verify refresh token hash is cleared
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == "test_logout@example.com"))
            user = result.scalars().first()
            assert user.refresh_token_hash is None

