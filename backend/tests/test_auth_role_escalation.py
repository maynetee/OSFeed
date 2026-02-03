import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from fastapi_users.password import PasswordHelper

from app.main import app
from app.database import AsyncSessionLocal, init_db
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_register_default_role_is_viewer():
    """Verify new users get VIEWER role by default."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={"email": "test_default_role@example.com", "password": "Str0ngP@ssword!"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test_default_role@example.com"
        assert data["role"] == UserRole.VIEWER.value
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert data["is_superuser"] is False

    # Verify user has VIEWER role in DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "test_default_role@example.com"))
        user = result.scalars().first()
        assert user is not None
        assert user.role == UserRole.VIEWER


@pytest.mark.asyncio
async def test_register_with_admin_role_ignored():
    """Verify attempting to register with role=admin is ignored and VIEWER is used."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Attempt to register with admin role
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test_admin_attempt@example.com",
                "password": "Str0ngP@ssword!",
                "role": "admin"
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test_admin_attempt@example.com"
        # Should be VIEWER, not admin
        assert data["role"] == UserRole.VIEWER.value
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert data["is_superuser"] is False

    # Verify user has VIEWER role in DB (not admin)
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "test_admin_attempt@example.com"))
        user = result.scalars().first()
        assert user is not None
        assert user.role == UserRole.VIEWER
        assert user.role != UserRole.ADMIN


@pytest.mark.asyncio
async def test_register_with_analyst_role_ignored():
    """Verify attempting to register with role=analyst is ignored and VIEWER is used."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Attempt to register with analyst role
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test_analyst_attempt@example.com",
                "password": "Str0ngP@ssword!",
                "role": "analyst"
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test_analyst_attempt@example.com"
        # Should be VIEWER, not analyst
        assert data["role"] == UserRole.VIEWER.value
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert data["is_superuser"] is False

    # Verify user has VIEWER role in DB (not analyst)
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "test_analyst_attempt@example.com"))
        user = result.scalars().first()
        assert user is not None
        assert user.role == UserRole.VIEWER
        assert user.role != UserRole.ANALYST


@pytest.mark.asyncio
async def test_existing_admin_users_unaffected():
    """Verify existing admin users are not affected by the fix."""
    await init_db()
    password_helper = PasswordHelper()

    # Create an admin user directly in the database
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "test_existing_admin@example.com"))
        existing_user = result.scalars().first()

        if not existing_user:
            user = User(
                email="test_existing_admin@example.com",
                hashed_password=password_helper.hash("Str0ngP@ssword!"),
                is_active=True,
                is_superuser=True,
                is_verified=True,
                role=UserRole.ADMIN,
            )
            session.add(user)
            await session.commit()

    # Verify admin user still has admin role
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "test_existing_admin@example.com"))
        user = result.scalars().first()
        assert user is not None
        assert user.role == UserRole.ADMIN
        assert user.is_superuser is True
        assert user.is_verified is True

    # Login as admin user to verify functionality
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "test_existing_admin@example.com",
                "password": "Str0ngP@ssword!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_with_superuser_flag_ignored():
    """Verify attempting to register with is_superuser=true is ignored (FastAPI-Users safe mode)."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Attempt to register with superuser flag
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test_superuser_attempt@example.com",
                "password": "Str0ngP@ssword!",
                "is_superuser": True
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test_superuser_attempt@example.com"
        assert data["role"] == UserRole.VIEWER.value
        # is_superuser should be False
        assert data["is_superuser"] is False
        assert data["is_active"] is True
        assert data["is_verified"] is False

    # Verify user is not superuser in DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "test_superuser_attempt@example.com"))
        user = result.scalars().first()
        assert user is not None
        assert user.role == UserRole.VIEWER
        assert user.is_superuser is False


@pytest.mark.asyncio
async def test_register_with_is_verified_flag_ignored():
    """Verify attempting to register with is_verified=true is ignored (FastAPI-Users safe mode)."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Attempt to register with verified flag
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test_verified_attempt@example.com",
                "password": "Str0ngP@ssword!",
                "is_verified": True
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test_verified_attempt@example.com"
        assert data["role"] == UserRole.VIEWER.value
        # is_verified should be False
        assert data["is_verified"] is False
        assert data["is_active"] is True
        assert data["is_superuser"] is False

    # Verify user is not verified in DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "test_verified_attempt@example.com"))
        user = result.scalars().first()
        assert user is not None
        assert user.role == UserRole.VIEWER
        assert user.is_verified is False


@pytest.mark.asyncio
async def test_register_with_multiple_privilege_escalation_attempts():
    """Verify multiple privilege escalation attempts are all blocked."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Attempt to register with admin role, superuser, and verified flags
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test_multi_escalation@example.com",
                "password": "Str0ngP@ssword!",
                "role": "admin",
                "is_superuser": True,
                "is_verified": True,
                "is_active": True
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test_multi_escalation@example.com"
        # All privilege escalation attempts should be blocked
        assert data["role"] == UserRole.VIEWER.value
        assert data["is_superuser"] is False
        assert data["is_verified"] is False
        assert data["is_active"] is True

    # Verify user has minimal privileges in DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "test_multi_escalation@example.com"))
        user = result.scalars().first()
        assert user is not None
        assert user.role == UserRole.VIEWER
        assert user.is_superuser is False
        assert user.is_verified is False
