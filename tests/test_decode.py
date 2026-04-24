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
    assert isinstance(decoded[1], dict)

    inner_decoded = decoded[1]
    assert inner_decoded[102] == nickname_val

def test_proto_recursive_decoding():
    # Test that field IDs 1-9 are automatically decoded by Strategy B
    # Field 1 (Account): Tag 10
    # Field 101 (UID): Tag (101 << 3 | 2) = 810
    uid_val = b"9999"
    acc_payload = b"\xaa\x06" + encode_varint(len(uid_val)) + uid_val
    full_payload = b"\x0a" + encode_varint(len(acc_payload)) + acc_payload

    decoded = decode_response(full_payload)
    assert isinstance(decoded[1], dict)
    assert decoded[1][101] == uid_val

def test_rank_translation():
    from config.ranks import get_rank_name
    assert get_rank_name(601) == "Heroic"
    assert get_rank_name(101) == "Bronze I"
    assert get_rank_name(None) == "Unknown"

def test_decode_error_handling():
    from api.errors import FFError, ErrorCode
    # Test with invalid encrypted data (should trigger FM-04 detection if logic allows)
    # FM-04: AES Decryption failure
    with pytest.raises(FFError) as excinfo:
        decode_player_data(b"too-short")
    assert excinfo.value.code == ErrorCode.DECODE_ERROR
    assert excinfo.value.extra is not None
    assert excinfo.value.extra.get("possible_key_rotation") is True
