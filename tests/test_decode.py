import pytest
from core.crypto import aes_encrypt, aes_decrypt
from core.proto import encode_request, decode_response, encode_varint
from core.decoder import decode_player_data
from api.schemas import PlayerData

def test_aes_round_trip():
    original = b"hello world 123"
    encrypted = aes_encrypt(original)
    decrypted = aes_decrypt(encrypted)
    assert decrypted == original

def test_proto_request_encode():
    encoded = encode_request("12345", "IND", "OB53")
    assert isinstance(encoded, bytes)
    assert len(encoded) > 0

def test_proto_response_decode_nested():
    # Construct a nested payload
    # Field 1 (AccountInfo): Tag (1 << 3 | 2) = 10
    # Inside AccountInfo: Field 102 (nickname): Tag (102 << 3 | 2) = 818
    nickname_val = b"Test"
    inner_payload = b"\xb2\x06" + encode_varint(len(nickname_val)) + nickname_val
    outer_payload = b"\x0a" + encode_varint(len(inner_payload)) + inner_payload

    decoded = decode_response(outer_payload)
    assert 1 in decoded
    # Strategy B is now recursive for field ID 1
    assert isinstance(decoded[1], dict)
    assert decoded[1][102] == nickname_val

def test_rank_translation():
    from config.ranks import get_rank_name
    assert get_rank_name(601) == "Heroic"
    assert get_rank_name(101) == "Bronze I"
    assert get_rank_name(None) == "Unknown"
