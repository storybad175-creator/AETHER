import pytest
import asyncio
import json
import time
from unittest.mock import MagicMock, AsyncMock
from config.settings import settings
from api.errors import FFError, ErrorCode

@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setattr(settings, "GARENA_GUEST_UID", "test_uid")
    monkeypatch.setattr(settings, "GARENA_GUEST_TOKEN", "test_token")
    monkeypatch.setattr(settings, "AES_KEY", "00" * 32)
    monkeypatch.setattr(settings, "AES_IV", "00" * 16)
    return settings

@pytest.fixture
def sample_uid():
    return "4899748638"

@pytest.fixture
def sample_region():
    return "IND"

@pytest.fixture
def mock_encrypted_response():
    # This would be real AES-encrypted protobuf in a full mock,
    # for now we'll mock the transport to return this and the decoder to handle it.
    return b"encrypted_data_stub"

@pytest.fixture
def mock_jwt():
    return "mocked_jwt_token"
