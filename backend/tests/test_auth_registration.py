import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from fastapi_users.password import PasswordHelper

from app.main import app
from app.database import AsyncSessionLocal, init_db
from app.models.user import User


@pytest.mark.asyncio
async def test_register_success():
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={"email": "test_register_new@example.com", "password": "Str0ngP@ssword!"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test_register_new@example.com"
        assert data["is_active"] is True
        assert data["is_verified"] is False

    # Verify user exists in DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "test_register_new@example.com"))
        user = result.scalars().first()
        assert user is not None
        assert user.email == "test_register_new@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email():
    await init_db()
    password_helper = PasswordHelper()

    # Create existing user
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "test_register_dup@example.com"))
        existing_user = result.scalars().first()

        if not existing_user:
            user = User(
                email="test_register_dup@example.com",
                hashed_password=password_helper.hash("Str0ngP@ssword!"),
                is_active=True,
                is_superuser=False,
                is_verified=False,
            )
            session.add(user)
            await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={"email": "test_register_dup@example.com", "password": "Str0ngP@ssword!"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "REGISTER_USER_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_forgot_password_returns_202():
    await init_db()
    password_helper = PasswordHelper()

    # Create user for forgot-password
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "test_forgot_pw@example.com"))
        existing_user = result.scalars().first()

        if not existing_user:
            user = User(
                email="test_forgot_pw@example.com",
                hashed_password=password_helper.hash("Str0ngP@ssword!"),
                is_active=True,
                is_superuser=False,
                is_verified=True,
            )
            session.add(user)
            await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/forgot-password",
            json={"email": "test_forgot_pw@example.com"},
        )
        assert response.status_code == 202


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email_returns_202():
    """Forgot-password should return 202 even for unknown emails to prevent user enumeration."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/forgot-password",
            json={"email": "nonexistent_user@example.com"},
        )
        assert response.status_code == 202


@pytest.mark.asyncio
async def test_register_weak_password_too_short():
    """Registration should fail when password is less than 8 characters."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={"email": "test_short@example.com", "password": "Abc1!"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "REGISTER_INVALID_PASSWORD"
        assert "at least 8 characters" in data.get("reason", "").lower()


@pytest.mark.asyncio
async def test_register_weak_password_no_uppercase():
    """Registration should fail when password has no uppercase letter."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={"email": "test_no_upper@example.com", "password": "password123!"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "REGISTER_INVALID_PASSWORD"
        assert "uppercase" in data.get("reason", "").lower()


@pytest.mark.asyncio
async def test_register_weak_password_no_lowercase():
    """Registration should fail when password has no lowercase letter."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={"email": "test_no_lower@example.com", "password": "PASSWORD123!"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "REGISTER_INVALID_PASSWORD"
        assert "lowercase" in data.get("reason", "").lower()


@pytest.mark.asyncio
async def test_register_weak_password_no_digit():
    """Registration should fail when password has no digit."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={"email": "test_no_digit@example.com", "password": "Password!"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "REGISTER_INVALID_PASSWORD"
        assert "digit" in data.get("reason", "").lower()


@pytest.mark.asyncio
async def test_register_weak_password_no_special_char():
    """Registration should fail when password has no special character."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={"email": "test_no_special@example.com", "password": "Password123"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "REGISTER_INVALID_PASSWORD"
        assert "special character" in data.get("reason", "").lower()


@pytest.mark.asyncio
async def test_register_strong_password_success():
    """Registration should succeed with a strong password meeting all requirements."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={"email": "test_strong_pwd@example.com", "password": "Strong@Pass123!"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test_strong_pwd@example.com"
        assert data["is_active"] is True
        assert data["is_verified"] is False

    # Verify user exists in DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "test_strong_pwd@example.com"))
        user = result.scalars().first()
        assert user is not None
        assert user.email == "test_strong_pwd@example.com"
