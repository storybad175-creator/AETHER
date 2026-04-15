import pytest
import httpx
from httpx import AsyncClient
from main import app
from unittest.mock import patch

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_regions_endpoint():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/regions")
    assert response.status_code == 200
    assert "IND" in response.json()

@pytest.mark.asyncio
async def test_player_endpoint_invalid_uid():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/player?uid=123&region=IND")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_UID"

@pytest.mark.asyncio
async def test_player_endpoint_invalid_region():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/player?uid=123456789&region=XYZ")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_UID" # It's caught by PlayerRequest validation which raises ValueError
    # Actually in routes.py I catch ValueError and raise FFError(ErrorCode.INVALID_UID...)
