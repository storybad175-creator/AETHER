import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock
from config.settings import settings
from core.crypto import cipher

@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setattr(settings, "AES_KEY", "0" * 64)
    monkeypatch.setattr(settings, "AES_IV", "0" * 32)
    return settings

@pytest.fixture
def sample_uid():
    return "1234567890"

@pytest.fixture
def sample_region():
    return "IND"

@pytest.fixture
def mock_jwt():
    return "mock_jwt_token_12345"

@pytest.fixture
def mock_encrypted_response():
    # Mock some protobuf bytes
    raw_payload = b"\x08\xd2\t\x12\x03IND\x52\x08Nickname" # Simplified
    return cipher.encrypt(raw_payload)
