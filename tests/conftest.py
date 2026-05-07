import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch
from config.settings import settings

@pytest.fixture
def mock_settings():
    with patch("config.settings.settings") as mocked:
        mocked.AES_KEY = "0" * 64
        mocked.AES_IV = "0" * 32
        mocked.GARENA_GUEST_UID = "test_uid"
        mocked.GARENA_GUEST_TOKEN = "test_token"
        mocked.OB_VERSION = "OB53"
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
def mock_player_data_dict(sample_uid, sample_region):
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
                    "matches": 1420, "wins": 187, "win_rate": "13.17%", "kills": 3801,
                    "deaths": 1233, "kd_ratio": 3.08, "headshots": 1244, "headshot_rate": "32.73%",
                    "avg_damage_per_match": 632.40, "booyahs": 187
                },
                "duo": {
                    "matches": 980, "wins": 201, "win_rate": "20.51%", "kills": 2710,
                    "deaths": 779, "kd_ratio": 3.48, "headshots": 880, "headshot_rate": "32.47%",
                    "avg_damage_per_match": 701.20, "booyahs": 201
                },
                "squad": {
                    "matches": 2104, "wins": 540, "win_rate": "25.67%", "kills": 5501,
                    "deaths": 1564, "kd_ratio": 3.52, "headshots": 1802, "headshot_rate": "32.76%",
                    "avg_damage_per_match": 744.80, "booyahs": 540
                }
            },
            "clash_squad": {
                "ranked": {
                    "matches": 340, "wins": 198, "win_rate": "58.24%", "kills": 1120, "kd_ratio": 2.14
                }
            }
        },
        "social": {
            "guild": {
                "id": "3037982359", "name": "Ƭ͢ɴ_நா#கதா", "level": 3,
                "member_count": 30, "capacity": 30,
                "leader": {"uid": "1122334455", "nickname": "Leader_X", "level": 72, "rank_name": "Heroic"}
            }
        },
        "pet": {
            "name": "Night Panther", "level": 6, "exp": 4490, "active_skill": "Helping Hand",
            "skin_id": 8003, "is_selected": True
        },
        "cosmetics": {
            "avatar_id": 102001, "banner_id": 301044, "pin_id": 700012, "character_id": 4,
            "equipped_outfit_ids": [211001, 211002, 211003, 211004, 211005],
            "equipped_weapon_skin_ids": [907005, 907006]
        },
        "pass": {
            "booyah_pass_level": 50, "fire_pass_status": "Premium", "fire_pass_badge_count": 12
        },
        "credit": {
            "score": 100, "reward_claimed": True, "summary_period": "Season 38"
        },
        "ban": {
            "is_banned": False, "ban_period": None, "ban_type": None
        }
    }
