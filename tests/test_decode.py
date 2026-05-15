import pytest
from core.crypto import aes_encrypt, aes_decrypt
from core.proto import encode_request, decode_response, encode_varint
from core.decoder import decode_player_data
from api.schemas import PlayerData
import binascii

def test_aes_round_trip():
    original = b"hello world 123"
    encrypted = aes_encrypt(original)
    decrypted = aes_decrypt(encrypted)
    assert decrypted == original

def test_proto_request_encode():
    encoded = encode_request("12345", "IND", "OB53")
    assert isinstance(encoded, bytes)
    assert len(encoded) > 0

def test_proto_response_decode_recursive():
    # Construct a nested payload
    # Field 1 (AccountInfo): Tag (1 << 3 | 2) = 10
    # Inside AccountInfo: Field 102 (nickname): Tag (102 << 3 | 2) = 818 (binary: \xb2\x06)
    nickname_val = b"Test"
    inner_payload = b"\xb2\x06" + encode_varint(len(nickname_val)) + nickname_val
    outer_payload = b"\x0a" + encode_varint(len(inner_payload)) + inner_payload

    decoded = decode_response(outer_payload)
    assert 1 in decoded
    # Recursive decode should have turned Field 1 into a dict
    assert isinstance(decoded[1], dict)
    assert decoded[1][102] == nickname_val

def test_full_decode_to_model():
    # Construct a minimal full payload
    # Field 1 (Account): Field 101 (UID): Tag (101 << 3 | 2) = 810 (\xaa\x06)
    uid_val = b"123456"
    acc_payload = b"\xaa\x06" + encode_varint(len(uid_val)) + uid_val

    # Field 2 (Rank): Field 201 (BR Rank Code): Tag (201 << 3 | 0) = 1608 (\xc8\x0c)
    rank_payload = b"\xc8\x0c" + encode_varint(601)

    full_payload = (
        b"\x0a" + encode_varint(len(acc_payload)) + acc_payload +
        b"\x12" + encode_varint(len(rank_payload)) + rank_payload
    )

    encrypted = aes_encrypt(full_payload)
    model = decode_player_data(encrypted)

    assert isinstance(model, PlayerData)
    assert model.account.uid == "123456"
    assert model.rank.battle_royale.rank_name == "Heroic"

def test_iso_timestamp_conversion():
    # Field 1 (Account): Field 113 (created_at_epoch): Tag (113 << 3 | 0) = 904 (\x88\x07)
    # AND must include UID (Field 101) to pass Pydantic validation
    uid_val = b"123456"
    epoch = 1641513600 # 2022-01-07
    acc_payload = (
        b"\xaa\x06" + encode_varint(len(uid_val)) + uid_val +
        b"\x88\x07" + encode_varint(epoch)
    )
    full_payload = b"\x0a" + encode_varint(len(acc_payload)) + acc_payload

    model = decode_player_data(aes_encrypt(full_payload))
    assert model.account.created_at == "2022-01-07T00:00:00Z"

def test_rank_translation():
    from config.ranks import get_rank_name
    assert get_rank_name(601) == "Heroic"
    assert get_rank_name(101) == "Bronze I"
    assert get_rank_name(None) == "Unknown"
