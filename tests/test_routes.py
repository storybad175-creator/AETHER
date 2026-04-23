import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_regions_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/regions")
    assert response.status_code == 200
    assert "IND" in response.json()
    assert len(response.json()) == 14

@pytest.mark.asyncio
async def test_player_invalid_uid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/player?uid=123&region=IND")
    assert response.status_code == 400
    # Our middleware now returns metadata and error structure
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_UID"

@pytest.mark.asyncio
async def test_batch_endpoint_limit():
    # Test batch up to 10 UIDs
    uids = ",".join([str(i) for i in range(100000, 100012)]) # 12 UIDs
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/batch?uids={uids}&region=IND")
    assert response.status_code == 200
    assert len(response.json()) == 10 # Should be limited to 10
