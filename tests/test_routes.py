import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from unittest.mock import patch, AsyncMock

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
    assert "INVALID_UID" in response.json()["error"]["code"]

@pytest.mark.asyncio
async def test_player_invalid_region():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/player?uid=12345678&region=INVALID")
    assert response.status_code == 400
    assert "INVALID_REGION" in response.json()["error"]["code"]

@pytest.mark.asyncio
async def test_player_endpoint_not_found():
    from api.errors import FFError, ErrorCode
    with patch("api.routes.fetch_player", side_effect=FFError(ErrorCode.PLAYER_NOT_FOUND, "Not Found")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/player?uid=12345678&region=IND")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PLAYER_NOT_FOUND"

@pytest.mark.asyncio
async def test_player_endpoint_valid(mock_player_data_dict):
    mock_resp = {
        "metadata": {
            "request_uid": "12345678",
            "request_region": "IND",
            "fetched_at": "2026-04-11T14:32:07Z",
            "response_time_ms": 10,
            "api_version": "OB53",
            "cache_hit": False
        },
        "data": mock_player_data_dict,
        "error": None
    }
    with patch("api.routes.fetch_player", return_value=mock_resp):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/player?uid=12345678&region=IND")
    assert response.status_code == 200
    assert response.json()["data"]["account"]["nickname"] == "Ƭɴɪᴛᴀᴄʜɪ"

@pytest.mark.asyncio
async def test_batch_endpoint(mock_player_data_dict):
    from api.errors import FFError, ErrorCode

    async def side_effect(uid, region):
        if uid == "99999999":
            raise FFError(ErrorCode.PLAYER_NOT_FOUND, "Not Found")
        return {
            "metadata": {
                "request_uid": uid,
                "request_region": region,
                "fetched_at": "2026-04-11T14:32:07Z",
                "response_time_ms": 10,
                "api_version": "OB53",
                "cache_hit": False
            },
            "data": mock_player_data_dict,
            "error": None
        }

    with patch("api.routes.fetch_player", side_effect=side_effect):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/batch?uids=12345678,99999999&region=IND")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["error"] is None
    assert data[1]["error"]["code"] == "PLAYER_NOT_FOUND"

@pytest.mark.asyncio
async def test_rate_limit_middleware():
    from config.settings import settings
    with patch.object(settings, 'RATE_LIMIT_RPM', 2):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # First request
            await ac.get("/health")
            # Second request
            await ac.get("/health")
            # Third request - should be rate limited
            response = await ac.get("/health")

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "RATE_LIMITED"
