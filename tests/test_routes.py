import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock, patch
from api.schemas import PlayerResponse

client = TestClient(app)

@pytest.mark.asyncio
async def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_regions_endpoint():
    response = client.get("/api/v1/regions")
    assert response.status_code == 200
    assert "IND" in response.json()

@patch("api.routes.fetch_player")
def test_player_endpoint_valid(mock_fetch):
    mock_fetch.return_value = AsyncMock() # Should return a PlayerResponse object

    # We need a real PlayerResponse object for the response_model to work
    from api.schemas import PlayerResponse, ResponseMetadata, PlayerData
    from datetime import datetime

    mock_res = PlayerResponse(
        metadata=ResponseMetadata(
            request_uid="12345678",
            request_region="IND",
            fetched_at=datetime.now().isoformat(),
            response_time_ms=100,
            api_version="OB53",
            cache_hit=False
        ),
        data=None, # For simplicity
        error=None
    )
    mock_fetch.return_value = mock_res

    response = client.get("/api/v1/player?uid=12345678&region=IND")
    assert response.status_code == 200
    assert response.json()["metadata"]["request_uid"] == "12345678"

def test_player_endpoint_invalid_uid():
    response = client.get("/api/v1/player?uid=123&region=IND")
    # Pydantic validation error will be caught by our middleware and converted to FFError/400
    # Wait, FastAPI might catch it first as 422 Unprocessable Entity if not handled.
    # Our middleware handles FFError, but Pydantic raises ValidationError.
    assert response.status_code in [400, 422]
