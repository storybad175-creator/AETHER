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

@pytest.mark.asyncio
async def test_player_invalid_uid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/player?uid=123&region=IND")
    assert response.status_code == 400
    # My enhancement added granular INVALID_UID code
    assert "INVALID_UID" in response.text
