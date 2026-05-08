import pytest
import asyncio
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from main import app
from api.errors import ErrorCode

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
        assert "IND" in response.json()["regions"]

@pytest.mark.asyncio
async def test_player_invalid_uid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/player?uid=123&region=IND")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_UID"

@pytest.mark.asyncio
async def test_player_invalid_region():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/player?uid=123456789&region=XYZ")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_REGION"

@pytest.mark.asyncio
async def test_rate_limit(mock_settings):
    # Setting RPM to 2 for testing
    mock_settings.RATE_LIMIT_RPM = 2
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # First 2 should pass (or fail with 503 if we don't mock fetcher, but status won't be 429)
            await ac.get("/health")
            await ac.get("/health")

            # 3rd should be 429
            response = await ac.get("/health")
            assert response.status_code == 429
            assert response.json()["error"]["code"] == "RATE_LIMITED"
