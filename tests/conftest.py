import pytest
import time
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from api.errors import FFError, ErrorCode

from config.settings import settings as real_settings

@pytest.fixture
def mock_settings():
    """Patches the real settings object attributes for testing."""
    old_values = {
        "AES_KEY": real_settings.AES_KEY,
        "AES_IV": real_settings.AES_IV,
        "GARENA_GUEST_UID": real_settings.GARENA_GUEST_UID,
        "GARENA_GUEST_TOKEN": real_settings.GARENA_GUEST_TOKEN,
        "RATE_LIMIT_RPM": real_settings.RATE_LIMIT_RPM
    }

    real_settings.AES_KEY = "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff"
    real_settings.AES_IV = "00112233445566778899aabbccddeeff"
    real_settings.GARENA_GUEST_UID = "12345"
    real_settings.GARENA_GUEST_TOKEN = "mock_token"
    real_settings.RATE_LIMIT_RPM = 30

    yield real_settings

    for k, v in old_values.items():
        setattr(real_settings, k, v)

@pytest.fixture
def sample_player_data():
    return {
        "account": {
            "uid": "4899748638",
            "nickname": "Ƭɴɪᴛᴀᴄʜɪ",
            "level": 60,
            "exp": 964636,
            "region": "IND",
            "season_id": 38,
            "preferred_mode": "Battle Royale",
            "language": "English",
            "signature": "CHANDRU HERE...!!!",
            "honor_score": 100,
            "total_likes": 5817,
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
                "rank_code": 114,
                "points": 2541,
                "max_rank_name": "Diamond I",
                "max_rank_code": 115,
                "visible": True
            },
            "clash_squad": {
                "rank_name": "Gold III",
                "rank_code": 209,
                "points": 261,
                "visible": True
            }
        },
        "stats": {
            "battle_royale": {
                "solo": {"matches": 10, "wins": 1, "win_rate": "10.00%", "kills": 20, "deaths": 9, "kd_ratio": 2.22, "headshots": 5, "headshot_rate": "25.00%", "avg_damage_per_match": 500.0, "booyahs": 1},
                "duo": {"matches": 10, "wins": 1, "win_rate": "10.00%", "kills": 20, "deaths": 9, "kd_ratio": 2.22, "headshots": 5, "headshot_rate": "25.00%", "avg_damage_per_match": 500.0, "booyahs": 1},
                "squad": {"matches": 10, "wins": 1, "win_rate": "10.00%", "kills": 20, "deaths": 9, "kd_ratio": 2.22, "headshots": 5, "headshot_rate": "25.00%", "avg_damage_per_match": 500.0, "booyahs": 1}
            },
            "clash_squad": {
                "ranked": {"matches": 100, "wins": 60, "win_rate": "60.00%", "kills": 200, "kd_ratio": 5.0}
            }
        },
        "social": {"guild": None},
        "pet": None,
        "cosmetics": {
            "avatar_id": 1, "banner_id": 2, "pin_id": 3, "character_id": 4,
            "equipped_outfit_ids": [101], "equipped_weapon_skin_ids": [201]
        },
        "pass": {"booyah_pass_level": 50, "fire_pass_status": "Premium", "fire_pass_badge_count": 100},
        "credit": {"score": 100, "reward_claimed": True, "summary_period": "Season 38"},
        "ban": {"is_banned": False, "ban_period": None, "ban_type": None}
    }

@pytest.fixture
def mock_jwt():
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQwNzA4ODAwMDB9.mock_signature"
