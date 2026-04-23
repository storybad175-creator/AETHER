"""
Shared pytest fixtures and mocks for the Free Fire API test suite.
"""
import pytest
import time
import json
from unittest.mock import AsyncMock, patch, MagicMock
from core.transport import AsyncTransport
from api.schemas import PlayerResponse, ResponseMetadata, PlayerData, ErrorDetail

@pytest.fixture
def mock_settings():
    with patch("config.settings.settings") as mock:
        mock.OB_VERSION = "OB53"
        mock.GARENA_GUEST_UID = "test_uid"
        mock.GARENA_GUEST_TOKEN = "test_token"
        mock.AES_KEY = "00" * 32
        mock.AES_IV = "00" * 16
        mock.CACHE_TTL_SECONDS = 300
        mock.CACHE_MAX_ENTRIES = 500
        mock.RATE_LIMIT_RPM = 30
        mock.LOG_LEVEL = "INFO"
        yield mock

@pytest.fixture
def sample_player_data():
    return {
        "account": {
            "uid": "123456789",
            "nickname": "TestPlayer",
            "level": 50,
            "exp": 100000,
            "region": "IND",
            "season_id": 38,
            "preferred_mode": "Battle Royale",
            "language": "English",
            "signature": "Hello World",
            "honor_score": 100,
            "total_likes": 1000,
            "ob_version": "OB53",
            "created_at_epoch": 1641513600,
            "created_at": "2022-01-07T00:00:00Z",
            "last_login_epoch": 1735862400,
            "last_login": "2025-01-03T00:00:00Z",
            "account_type": "Normal"
        },
        "rank": {
            "battle_royale": {
                "rank_name": "Platinum IV",
                "rank_code": 404,
                "points": 2500,
                "max_rank_name": "Diamond",
                "max_rank_code": 501,
                "visible": True
            },
            "clash_squad": {
                "rank_name": "Gold III",
                "rank_code": 303,
                "points": 200,
                "visible": True
            }
        },
        "stats": {
            "battle_royale": {
                "solo": {"matches": 10, "wins": 1, "win_rate": "10.00%", "kills": 30, "deaths": 9, "kd_ratio": 3.33, "headshots": 10, "headshot_rate": "33.33%", "avg_damage_per_match": 500.0, "booyahs": 1},
                "duo": {"matches": 0, "wins": 0, "win_rate": "0.00%", "kills": 0, "deaths": 0, "kd_ratio": 0.0, "headshots": 0, "headshot_rate": "0.00%", "avg_damage_per_match": 0.0, "booyahs": 0},
                "squad": {"matches": 0, "wins": 0, "win_rate": "0.00%", "kills": 0, "deaths": 0, "kd_ratio": 0.0, "headshots": 0, "headshot_rate": "0.00%", "avg_damage_per_match": 0.0, "booyahs": 0}
            },
            "clash_squad": {
                "ranked": {"matches": 5, "wins": 3, "win_rate": "60.00%", "kills": 15, "kd_ratio": 7.5}
            }
        },
        "social": {"guild": None},
        "pet": None,
        "cosmetics": {
            "avatar_id": 1, "banner_id": 1, "pin_id": 1, "character_id": 1,
            "equipped_outfit_ids": [1, 2], "equipped_weapon_skin_ids": [3]
        },
        "pass": {
            "booyah_pass_level": 10,
            "fire_pass_status": "Basic",
            "fire_pass_badge_count": 5
        },
        "credit": {"score": 100, "reward_claimed": False, "summary_period": "Season 38"},
        "ban": {"is_banned": False, "ban_period": None, "ban_type": None}
    }

@pytest.fixture
def mock_player_response(sample_player_data):
    return PlayerResponse(
        metadata=ResponseMetadata(
            request_uid="123456789",
            request_region="IND",
            fetched_at="2026-04-11T14:32:07Z",
            response_time_ms=100,
            api_version="OB53",
            cache_hit=False
        ),
        data=sample_player_data
    )

@pytest.fixture
def mock_transport():
    with patch("core.transport.transport", spec=AsyncTransport) as mock:
        mock.post = AsyncMock(return_value=b"mock_response")
        mock.session = MagicMock()
        yield mock

@pytest.fixture
def mock_jwt():
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MzU4NjI0MDB9.mock_signature"
