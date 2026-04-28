import pytest
import binascii
from core.crypto import aes_encrypt, aes_decrypt
from core.proto import encode_request, decode_response, encode_varint
from core.decoder import decode_player_data
from api.errors import FFError, ErrorCode

def test_aes_round_trip(mock_settings):
    data = b"hello world 123!!"
    encrypted = aes_encrypt(data)
    decrypted = aes_decrypt(encrypted)
    assert decrypted == data

def test_aes_decryption_failure(mock_settings):
    with pytest.raises(FFError) as exc:
        aes_decrypt(b"invalid data")
    assert exc.value.code == ErrorCode.DECODE_ERROR
    assert exc.value.extra.get("possible_key_rotation") is True

def test_proto_encode_request():
    proto_bytes = encode_request("12345", "IND", "OB53")
    assert isinstance(proto_bytes, bytes)
    assert len(proto_bytes) > 0

def test_proto_decode_response_strategy_b():
    # Construct a simple length-delimited msg: field 1 (account) containing field 101 (uid)="123"
    # Tag for field 1, type 2: (1 << 3) | 2 = 10
    # Inner: Tag for field 101, type 2: (101 << 3) | 2 = 810 -> [0xaa, 0x06] (varint)
    # "123" -> [0x31, 0x32, 0x33]
    inner = b'\xaa\x06\x03123'
    outer = b'\x0a' + bytes([len(inner)]) + inner

    decoded = decode_response(outer)
    assert 1 in decoded
    assert decoded[1][101] == b"123"

def test_full_decode_pipeline(mock_settings):
    """
    Gold standard integration test for the decoding pipeline.
    Constructs a real binary payload with nested structures and verifies mapping.
    """
    def pack_msg(field_id: int, inner_bytes: bytes) -> bytes:
        tag = (field_id << 3) | 2
        return encode_varint(tag) + encode_varint(len(inner_bytes)) + inner_bytes

    def pack_str(field_id: int, val: str) -> bytes:
        data = val.encode('utf-8')
        tag = (field_id << 3) | 2
        return encode_varint(tag) + encode_varint(len(data)) + data

    def pack_varint(field_id: int, val: int) -> bytes:
        tag = (field_id << 3) | 0
        return encode_varint(tag) + encode_varint(val)

    # 1. Build Account (nested in field 1)
    acc = pack_str(101, "4899748638") + pack_str(102, "Ƭɴɪᴛᴀᴄʜɪ") + pack_varint(103, 60)

    # 2. Build Rank (nested in field 2)
    rank = pack_varint(201, 601) + pack_varint(202, 2541) # Heroic

    # 3. Build Stats (nested in field 3)
    # solo is nested in 301
    solo = pack_varint(401, 100) + pack_varint(402, 10) + pack_varint(403, 500)
    stats = pack_msg(301, solo)

    # 4. Build Cosmetics (nested in field 6)
    cosm = pack_varint(701, 102001)

    # Assemble final message
    full_msg = pack_msg(1, acc) + pack_msg(2, rank) + pack_msg(3, stats) + pack_msg(6, cosm)

    # Encrypt
    encrypted = aes_encrypt(full_msg)

    # Decode
    player_data = decode_player_data(encrypted)

    # Assertions
    assert player_data.account.uid == "4899748638"
    assert player_data.account.nickname == "Ƭɴɪᴛᴀᴄʜɪ"
    assert player_data.account.level == 60
    assert player_data.rank.battle_royale.rank_name == "Heroic"
    assert player_data.stats.battle_royale.solo.matches == 100
    assert player_data.stats.battle_royale.solo.wins == 10
    assert player_data.stats.battle_royale.solo.kills == 500
    assert player_data.cosmetics.avatar_id == 102001
