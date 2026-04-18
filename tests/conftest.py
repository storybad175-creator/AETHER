import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from core.transport import AsyncTransport
from config.settings import settings
from api.schemas import PlayerResponse, PlayerData

@pytest.fixture
def mock_settings():
    with patch("config.settings.settings") as mocked:
        mocked.garena_guest_uid = "test_uid"
        mocked.garena_guest_token = "test_token"
        mocked.aes_key = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
        mocked.aes_iv = "000102030405060708090a0b0c0d0e0f"
        mocked.cache_ttl_seconds = 300
        mocked.cache_max_entries = 500
        mocked.ob_version = "OB53"
        yield mocked

@pytest.fixture
def sample_uid():
    return "4899748638"

@pytest.fixture
def sample_region():
    return "IND"

@pytest.fixture
def mock_jwt():
    return "mock.jwt.token"

@pytest.fixture
def mock_raw_player_dict():
    return {
        "account": {
            "uid": "4899748638",
            "nickname": "TestPlayer",
            "level": 60,
            "exp": 123456,
            "created_at_epoch": 1641513600,
            "last_login_epoch": 1735862400
        },
        "rank": {
            "battle_royale": {"rank_code": 404, "points": 2541},
            "clash_squad": {"rank_code": 203, "points": 261}
        },
        "stats": {
            "battle_royale": {
                "solo": {"matches": 100, "wins": 10, "kills": 300, "deaths": 90, "headshots": 50, "avg_damage_per_match": 500.0}
            }
        },
        "cosmetics": {"avatar_id": 1, "banner_id": 2},
        "pass_info": {"booyah_pass_level": 50},
        "credit": {"score": 100},
        "ban": {"is_banned": False}
    }
