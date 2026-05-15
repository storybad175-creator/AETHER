import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from unittest.mock import patch, AsyncMock
from api.schemas import PlayerResponse, ResponseMetadata

@pytest.fixture
def mock_player_response():
    # Construct a valid minimal PlayerResponse for mocking
    return {
        "metadata": {
            "request_uid": "1234567",
            "request_region": "IND",
            "fetched_at": "2026-04-11T14:32:07Z",
            "response_time_ms": 100,
            "api_version": "OB53",
            "cache_hit": False
        },
        "data": {
            "account": {"uid": "1234567", "nickname": "TestUser", "level": 10, "account_type": "Normal"},
            "rank": {
                "battle_royale": {"rank_name": "Bronze I", "rank_code": 101, "points": 100, "visible": True},
                "clash_squad": {"rank_name": "Unranked", "rank_code": 0, "points": 0, "visible": True}
            },
            "stats": {
                "battle_royale": {
                    "solo": {"matches": 0, "wins": 0, "kills": 0, "deaths": 0, "headshots": 0},
                    "duo": {"matches": 0, "wins": 0, "kills": 0, "deaths": 0, "headshots": 0},
                    "squad": {"matches": 0, "wins": 0, "kills": 0, "deaths": 0, "headshots": 0}
                },
                "clash_squad": {"ranked": {"matches": 0, "wins": 0, "kills": 0}}
            },
            "social": {"guild": None},
            "cosmetics": {"avatar_id": 1, "banner_id": 1, "equipped_outfit_ids": [], "equipped_weapon_skin_ids": []},
            "pass": {"booyah_pass_level": 0, "fire_pass_status": "Basic", "fire_pass_badge_count": 0},
            "credit": {"score": 100, "reward_claimed": False},
            "ban": {"is_banned": False}
        },
        "error": None
    }

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
    assert response.json()["error"]["code"] == "INVALID_UID"

@pytest.mark.asyncio
async def test_player_invalid_region():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/player?uid=1234567&region=INVALID")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REGION"

@pytest.mark.asyncio
async def test_batch_endpoint_success(mock_player_response):
    # Mock return value should be a PlayerResponse object
    resp_obj = PlayerResponse(**mock_player_response)

    with patch("api.routes.fetch_player", return_value=resp_obj):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/batch?uids=1234567,8888888&region=IND")
        assert response.status_code == 200
        assert len(response.json()) == 2

@pytest.mark.asyncio
async def test_batch_endpoint_mixed_validation_error(mock_player_response):
    resp_obj = PlayerResponse(**mock_player_response)

    with patch("api.routes.fetch_player", return_value=resp_obj):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # One valid UID, one invalid (too short)
            response = await ac.get("/batch?uids=1234567,123&region=IND")

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
    # Second one should have an error
    assert results[1]["error"]["code"] == "INVALID_UID"
