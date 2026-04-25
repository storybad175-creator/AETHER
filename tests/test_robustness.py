import pytest
import asyncio
import socket
from httpx import AsyncClient, ASGITransport
from main import app
from api.schemas import PlayerResponse
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_batch_endpoint_success():
    """Tests the /batch endpoint with multiple valid UIDs."""
    # We need to mock fetch_player to avoid real network calls
    with patch("api.routes.fetch_player", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = PlayerResponse(
            metadata={
                "request_uid": "12345",
                "request_region": "IND",
                "fetched_at": "now",
                "response_time_ms": 10,
                "api_version": "OB53",
                "cache_hit": False
            },
            data=None # Simplified for test
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/batch?uids=12345,67890&region=IND")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["metadata"]["request_uid"] == "12345"

@pytest.mark.asyncio
async def test_batch_endpoint_partial_failure():
    """Tests the /batch endpoint where one UID is invalid."""
    with patch("api.routes.fetch_player", new_callable=AsyncMock) as mock_fetch:
        # First call succeeds, second is not reached for invalid UID
        # but our safe_fetch handles it
        mock_fetch.return_value = PlayerResponse(
            metadata={
                "request_uid": "123456",
                "request_region": "IND",
                "fetched_at": "now",
                "response_time_ms": 10,
                "api_version": "OB53",
                "cache_hit": False
            },
            data=None
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 123 is too short (invalid), 123456 is valid
            response = await ac.get("/batch?uids=123,123456&region=IND")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # First one should have an error
        assert data[0]["error"]["code"] == "INVALID_UID"
        # Second one should be success (mocked)
        assert data[1]["metadata"]["request_uid"] == "123456"

def test_port_conflict_resolution():
    """
    Simulates a port conflict and verifies that the logic finds the next available port.
    Tests the actual implementation in main.py.
    """
    from main import find_available_port

    base_port = 9000

    # Occupy the base port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", base_port))
        s.listen(1)

        # Call the actual implementation
        port = find_available_port(base_port)

        assert port == base_port + 1
