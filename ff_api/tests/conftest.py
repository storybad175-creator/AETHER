import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from ff_api.config.settings import settings
from ff_api.core.crypto import aes_encrypt

@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setattr(settings, "AES_KEY", "0123456789abcdef0123456789abcdef")
    monkeypatch.setattr(settings, "AES_IV", "0123456789abcdef")
    return settings

@pytest.fixture
def sample_uid():
    return "4899748638"

@pytest.fixture
def sample_region():
    return "IND"

@pytest.fixture
def mock_jwt():
    return "mock_jwt_token"

@pytest.fixture
def mock_player_raw_dict(sample_uid):
    return {
        "uid": int(sample_uid),
        "nickname": "Ƭɴɪᴛᴀᴄʜɪ",
        "level": 60,
        "exp": 964636,
        "region": "IND",
        "br_rank_code": 104,
        "br_points": 2541,
        "br_max_rank_code": 105,
        "cs_rank_code": 203,
        "cs_points": 261,
        "guild_id": "3037982359",
        "guild_name": "Ƭ͢ɴ_நா#கதா",
        "pet_name": "Night Panther",
        "pet_level": 6,
        "is_banned": False
    }
