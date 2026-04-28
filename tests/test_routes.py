import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock, patch
from api.schemas import PlayerResponse, ResponseMetadata, AccountInfo, ModeRankInfo, StatsInfo, SocialInfo, CosmeticsInfo, PassInfo, CreditInfo, BanInfo, PlayerData
from config.settings import settings

client = TestClient(app)

@pytest.fixture
def mock_fetch_player():
    with patch("api.routes.fetch_player", new_callable=AsyncMock) as mocked:
        yield mocked

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_regions_endpoint():
    response = client.get("/regions")
    assert response.status_code == 200
    assert "IND" in response.json()
    assert len(response.json()) == 14

def test_player_endpoint_valid(mock_fetch_player):
    mock_data = PlayerData(
        account=AccountInfo(uid="1234567", nickname="Test"),
        rank=ModeRankInfo(
            battle_royale={"rank_name": "Heroic"},
            clash_squad={"rank_name": "Gold"}
        ),
        stats=StatsInfo(
            battle_royale={"solo": {}, "duo": {}, "squad": {}},
            clash_squad={"ranked": {}}
        ),
        social=SocialInfo(),
        cosmetics=CosmeticsInfo(),
        pass_info=PassInfo(),
        credit=CreditInfo(),
        ban=BanInfo()
    )

    mock_fetch_player.return_value = PlayerResponse(
        metadata=ResponseMetadata(
            request_uid="1234567",
            request_region="IND",
            fetched_at="now",
            response_time_ms=10,
            api_version="OB53",
            cache_hit=False
        ),
        data=mock_data
    )

    response = client.get("/player?uid=1234567&region=IND")
    assert response.status_code == 200
    assert response.json()["data"]["account"]["nickname"] == "Test"

def test_player_endpoint_invalid_uid():
    response = client.get("/player?uid=123&region=IND")
    # FastAPI returns 422 for Query parameter validation failure (min_length=5)
    # Our custom validation in fetch_player would return 400 if it reached there
    assert response.status_code in [400, 422]

def test_rate_limit(mock_settings):
    # Reset visits for test isolation
    from api.middleware import RateLimitMiddleware
    # Find the middleware in app.user_middleware or similar is hard,
    # but we can try to hit the endpoint

    # We use a large number to ensure we hit the limit
    limit = 30 # Default

    for i in range(limit + 5):
        response = client.get("/health")
        if response.status_code == 429:
            break

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "RATE_LIMITED"
