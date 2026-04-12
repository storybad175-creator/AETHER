import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_regions_endpoint():
    response = client.get("/regions")
    assert response.status_code == 200
    assert "IND" in response.json()
    assert len(response.json()) == 14

@patch("api.routes.fetch_player", new_callable=AsyncMock)
def test_player_endpoint_valid(mock_fetch):
    mock_fetch.return_value = {
        "metadata": {
            "request_uid": "12345678",
            "request_region": "IND",
            "fetched_at": "2026-04-11T14:32:07Z",
            "response_time_ms": 100,
            "api_version": "OB53",
            "cache_hit": False
        },
        "data": {
            "account": {"uid": "12345678", "nickname": "Tester"},
            "rank": {
                "battle_royale": {"rank_name": "Heroic"},
                "clash_squad": {"rank_name": "Gold"}
            },
            "stats": {
                "battle_royale": {
                    "solo": {}, "duo": {}, "squad": {}
                },
                "clash_squad": {"ranked": {}}
            },
            "social": {"guild": None},
            "cosmetics": {},
            "pass": {"booyah_pass_level": 10},
            "credit": {"score": 100},
            "ban": {"is_banned": False}
        }
    }
    response = client.get("/player?uid=12345678&region=IND")
    assert response.status_code == 200
    assert response.json()["data"]["account"]["nickname"] == "Tester"

def test_player_endpoint_invalid_uid():
    response = client.get("/player?uid=123&region=IND")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_UID"

def test_rate_limit_middleware():
    # settings.RATE_LIMIT_RPM is 30 in mock_settings (well, if we used mock_settings here)
    # The default in settings.py is 30.
    for _ in range(30):
        client.get("/health")

    response = client.get("/health")
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "RATE_LIMITED"
