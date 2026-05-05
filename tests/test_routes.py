import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from unittest.mock import AsyncMock, patch
from api.schemas import PlayerResponse

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
    assert response.json()["error"]["code"] == "INVALID_INPUT"

@pytest.mark.asyncio
async def test_batch_endpoint_partial_failure():
    # Mock fetch_player to fail for one UID and succeed for another
    async def mock_fetch(uid, region):
        from api.errors import FFError, ErrorCode
        if uid == "111111111":
            raise FFError(ErrorCode.PLAYER_NOT_FOUND, "Not found")

        # Return a mock successful PlayerResponse
        from api.schemas import PlayerResponse, ResponseMetadata
        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at="now",
                response_time_ms=10,
                api_version="OB53",
                cache_hit=False
            ),
            data=None # Simplified for test
        )

    with patch("api.routes.fetch_player", side_effect=mock_fetch):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/batch?uids=111111111,222222222&region=IND")

        assert response.status_code == 200
        results = response.json()
        assert len(results) == 2

        # First one should have an error
        assert results[0]["error"]["code"] == "PLAYER_NOT_FOUND"
        # Second one should be successful
        assert results[1]["error"] is None
