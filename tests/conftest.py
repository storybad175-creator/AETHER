import pytest
import asyncio
import aiohttp
from unittest.mock import MagicMock, AsyncMock
from config.settings import settings
from core.crypto import aes_encrypt

@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setattr(settings, "AES_KEY", "6162636465666768696a6b6c6d6e6f707172737475767778797a313233343536")
    monkeypatch.setattr(settings, "AES_IV", "31323334353637383930313233343536")
    monkeypatch.setattr(settings, "GARENA_GUEST_UID", "test_guest_uid")
    monkeypatch.setattr(settings, "GARENA_GUEST_TOKEN", "test_guest_token")

@pytest.fixture
def sample_uid():
    return "4899748638"

@pytest.fixture
def sample_region():
    return "IND"

@pytest.fixture
def mock_jwt():
    return "mock_jwt_token_header.payload.signature"

@pytest.fixture
def mock_encrypted_response():
    # Construct a simple protobuf-like payload for testing
    # field 1: uid (string) "4899748638"
    # field 2: nickname (string) "Ƭɴɪᴛᴀᴄʜɪ"
    from core.proto import encode_varint

    def pack_field(fn, wt, val):
        tag = (fn << 3) | wt
        if wt == 2:
            content = val.encode('utf-8')
            return encode_varint(tag) + encode_varint(len(content)) + content
        return b''

    raw_proto = pack_field(1, 2, "4899748638") + pack_field(2, 2, "Ƭɴɪᴛᴀᴄʜɪ")
    return aes_encrypt(raw_proto)
