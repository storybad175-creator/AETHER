import pytest
import asyncio
from unittest.mock import MagicMock
from config.settings import settings as real_settings

@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Patches settings for test isolation."""
    # Directly modify the real_settings instance since it's used as a singleton
    monkeypatch.setattr(real_settings, "GARENA_GUEST_UID", "test_uid")
    monkeypatch.setattr(real_settings, "GARENA_GUEST_TOKEN", "test_token")
    monkeypatch.setattr(real_settings, "AES_KEY", "0" * 64)
    monkeypatch.setattr(real_settings, "AES_IV", "0" * 32)
    monkeypatch.setattr(real_settings, "CACHE_TTL_SECONDS", 3600)
    monkeypatch.setattr(real_settings, "RATE_LIMIT_RPM", 1000)
    return real_settings

@pytest.fixture
def sample_uid():
    return "1234567890"

@pytest.fixture
def sample_region():
    return "IND"

@pytest.fixture
def mock_jwt():
    return "mock.jwt.token"
