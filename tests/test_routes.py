import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from unittest.mock import patch, AsyncMock
from api.schemas import PlayerResponse, ResponseMetadata, PlayerData
import json

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
async def test_player_endpoint_invalid_uid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/player?uid=123&region=IND")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_UID"

@pytest.mark.asyncio
@patch("api.routes.fetch_player")
async def test_player_endpoint_valid(mock_fetch):
    mock_fetch.return_value = {
        "metadata": {
            "request_uid": "4899748638",
            "request_region": "IND",
            "fetched_at": "now",
            "response_time_ms": 100,
            "api_version": "OB53",
            "cache_hit": False
        },
        "data": None,
        "error": None
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/player?uid=4899748638&region=IND")

    assert response.status_code == 200
    assert response.json()["metadata"]["request_uid"] == "4899748638"
