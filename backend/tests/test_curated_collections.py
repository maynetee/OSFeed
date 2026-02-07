import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import init_db, AsyncSessionLocal
from app.models.collection import Collection
from app.seeds.curated_collections import seed_curated_collections


@pytest.fixture(autouse=True, scope="module")
async def _setup_db():
    """Ensure DB tables exist and seed curated collections for this test module."""
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_curated_collections(session)


@pytest.mark.asyncio
async def test_list_curated_collections():
    """Test that the curated collections endpoint returns a list."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/collections/curated")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check that returned items have expected fields
        first = data[0]
        assert "id" in first
        assert "name" in first
        assert "channel_count" in first
        assert "curated_channel_usernames" in first


@pytest.mark.asyncio
async def test_filter_curated_by_region():
    """Test filtering curated collections by region."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/collections/curated?region=Europe")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for item in data:
            assert item["region"] == "Europe"


@pytest.mark.asyncio
async def test_filter_curated_by_topic():
    """Test filtering curated collections by topic."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/collections/curated?topic=Conflict")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for item in data:
            assert item["topic"] == "Conflict"


@pytest.mark.asyncio
async def test_search_curated_collections():
    """Test searching curated collections by name."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/collections/curated?search=Ukraine")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_curated_collection_by_id():
    """Test getting a specific curated collection by ID."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First get the list to find a valid ID
        list_response = await client.get("/api/collections/curated")
        assert list_response.status_code == 200
        data = list_response.json()
        assert len(data) > 0

        collection_id = data[0]["id"]
        response = await client.get(f"/api/collections/curated/{collection_id}")
        assert response.status_code == 200
        detail = response.json()
        assert detail["id"] == collection_id
        assert "name" in detail
        assert "curated_channel_usernames" in detail


@pytest.mark.asyncio
async def test_get_curated_collection_not_found():
    """Test that getting a non-existent curated collection returns 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/collections/curated/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_import_requires_auth():
    """Test that importing a curated collection requires authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/collections/curated/00000000-0000-0000-0000-000000000000/import")
        assert response.status_code in [401, 403, 422]


@pytest.mark.asyncio
async def test_seed_is_idempotent():
    """Test that running seed twice doesn't create duplicates."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func
        result = await session.execute(
            select(func.count()).select_from(Collection).where(Collection.is_curated == True)
        )
        count_before = result.scalar()

    # Run seed again
    async with AsyncSessionLocal() as session:
        await seed_curated_collections(session)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count()).select_from(Collection).where(Collection.is_curated == True)
        )
        count_after = result.scalar()

    assert count_before == count_after
