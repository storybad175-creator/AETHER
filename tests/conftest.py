import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch
from config.settings import settings as real_settings

@pytest.fixture
def mock_settings():
    # Instead of patching the instance, we can patch the values on the real instance
    # to avoid issues with modules that already imported it.
    old_key = real_settings.AES_KEY
    old_iv = real_settings.AES_IV
    old_uid = real_settings.GARENA_GUEST_UID
    old_token = real_settings.GARENA_GUEST_TOKEN
    old_ob = real_settings.OB_VERSION

    real_settings.AES_KEY = "0" * 64
    real_settings.AES_IV = "0" * 32
    real_settings.GARENA_GUEST_UID = "test_uid"
    real_settings.GARENA_GUEST_TOKEN = "test_token"
    real_settings.OB_VERSION = "OB53"

    # Also re-init the cipher if it exists
    try:
        from core.crypto import cipher
        cipher.__init__()
    except ImportError:
        pass

    yield real_settings

    real_settings.AES_KEY = old_key
    real_settings.AES_IV = old_iv
    real_settings.GARENA_GUEST_UID = old_uid
    real_settings.GARENA_GUEST_TOKEN = old_token
    real_settings.OB_VERSION = old_ob

    try:
        from core.crypto import cipher
        cipher.__init__()
    except ImportError:
        pass

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
