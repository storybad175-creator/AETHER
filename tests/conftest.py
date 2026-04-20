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
def mock_player_data_dict():
    return {
        "uid": 4899748638,
        "nickname": "Ƭɴɪᴛᴀᴄʜɪ",
        "level": 60,
        "br_rank_code": 104,
        "br_points": 2541,
        "guild_id": 3037982359,
        "guild_name": "Ƭ͢ɴ_நா#கதா"
    }
