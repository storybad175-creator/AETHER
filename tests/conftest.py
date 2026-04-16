import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from config.settings import settings
from api.schemas import PlayerData

@pytest.fixture
def sample_uid():
    return "4899748638"

@pytest.fixture
def sample_region():
    return "IND"

@pytest.fixture
def mock_jwt():
    return "mock_jwt_token_123"

@pytest.fixture
def mock_player_data(sample_uid, sample_region):
    # This matches the Pydantic schema in api/schemas.py
    return {
        "account": {
            "uid": sample_uid,
            "nickname": "Ƭɴɪᴛᴀᴄʜɪ",
            "level": 60,
            "exp": 964636,
            "region": sample_region,
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
                "rank_code": 404,
                "points": 2541,
                "max_rank_name": "Diamond I",
                "max_rank_code": 501,
                "visible": True
            },
            "clash_squad": {
                "rank_name": "Gold III",
                "rank_code": 303,
                "points": 261,
                "visible": True
            }
        },
        "stats": {
            "battle_royale": {
                "solo": {
                    "matches": 10, "wins": 1, "win_rate": "10.00%", "kills": 30, "deaths": 9,
                    "kd_ratio": 3.33, "headshots": 10, "headshot_rate": "33.33%",
                    "avg_damage_per_match": 500.0, "booyahs": 1
                },
                "duo": {
                    "matches": 0, "wins": 0, "win_rate": "0.00%", "kills": 0, "deaths": 0,
                    "kd_ratio": 0.0, "headshots": 0, "headshot_rate": "0.00%",
                    "avg_damage_per_match": 0.0, "booyahs": 0
                },
                "squad": {
                    "matches": 0, "wins": 0, "win_rate": "0.00%", "kills": 0, "deaths": 0,
                    "kd_ratio": 0.0, "headshots": 0, "headshot_rate": "0.00%",
                    "avg_damage_per_match": 0.0, "booyahs": 0
                }
            },
            "clash_squad": {
                "matches": 5, "wins": 3, "win_rate": "60.00%", "kills": 20, "kd_ratio": 2.5
            }
        },
        "social": {"guild": None},
        "pet": None,
        "cosmetics": {
            "avatar_id": 1, "banner_id": 1, "pin_id": 1, "character_id": 1,
            "equipped_outfit_ids": [], "equipped_weapon_skin_ids": []
        },
        "pass": {
            "booyah_pass_level": 1, "fire_pass_status": "Basic", "fire_pass_badge_count": 0
        },
        "credit": {"score": 100, "reward_claimed": True, "summary_period": "S38"},
        "ban": {"is_banned": False, "ban_period": None, "ban_type": None}
    }
