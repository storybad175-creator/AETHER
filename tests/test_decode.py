import pytest
from core.proto import encode_varint, decode_varint, encode_request_raw, decode_response_raw
from core.crypto import aes_encrypt, aes_decrypt
from core.decoder import decode_player_data, format_iso

def test_varint_round_trip():
    values = [0, 1, 127, 128, 300, 16384, 1000000]
    for v in values:
        encoded = encode_varint(v)
        decoded, pos = decode_varint(encoded, 0)
        assert v == decoded
        assert pos == len(encoded)

def test_aes_round_trip(mock_settings):
    original = b"Hello World! This is a test."
    encrypted = aes_encrypt(original)
    decrypted = aes_decrypt(encrypted)
    assert original == decrypted

def test_format_iso():
    epoch = 1641513600 # 2022-01-07
    assert format_iso(epoch) == "2022-01-07T00:00:00Z"
    assert format_iso(None) is None

def test_proto_request_encode():
    encoded = encode_request_raw("12345", "IND", "OB53")
    assert isinstance(encoded, bytes)
    assert len(encoded) > 0

def test_proto_response_recursive_decode():
    # Build a simple nested message
    # Field 1 (Account) -> Field 101 (UID) = "4899748638"
    uid_bytes = "4899748638".encode('utf-8')
    # Inner: tag (101 << 3) | 2 = 810, length 10
    inner = encode_varint((101 << 3) | 2) + encode_varint(len(uid_bytes)) + uid_bytes
    # Outer: tag (1 << 3) | 2 = 10, length of inner
    outer = encode_varint((1 << 3) | 2) + encode_varint(len(inner)) + inner

    decoded = decode_response_raw(outer)
    assert 1 in decoded
    assert isinstance(decoded[1], dict)
    assert decoded[1][101] == b"4899748638"
