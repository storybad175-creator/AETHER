import pytest
import binascii
from core.crypto import aes_encrypt, aes_decrypt
from core.proto import encode_request, decode_response
from core.decoder import decode_player_data
from api.schemas import PlayerData

def test_proto_encode_decode():
    # Test Strategy B raw encoding
    uid = "123456789"
    region = "IND"
    version = "OB53"

    encoded = encode_request(uid, region, version)
    assert isinstance(encoded, bytes)
    assert len(encoded) > 0

    # We don't have a decoder for the request in core.proto (it only has decode_response_raw)
    # but we can check if it looks like protobuf
    # 1: uid, 2: region, 3: version
    decoded = decode_response(encoded)
    assert decoded[1].decode() == uid
    assert decoded[2].decode() == region
    assert decoded[3].decode() == version

def test_aes_round_trip(mock_settings):
    data = b"Hello Garena!"
    encrypted = aes_encrypt(data)
    assert encrypted != data

    decrypted = aes_decrypt(encrypted)
    assert decrypted == data

def test_full_decode_pipeline(mock_settings):
    # Mock some player data bytes
    # Strategy B uses Dict[int, Any]
    # We need to construct a realistic encrypted protobuf message
    # 101: uid, 102: nickname, 103: level
    acc_bytes = encode_request("4899748638", "Ƭɴɪᴛᴀᴄʜɪ", "60") # Reusing encode_request to get length-delimited bytes
    # But wait, encode_request uses field ids 1, 2, 3. We need 101, 102, 103.

    # Let's manually build a small response for testing decode_player_data
    # 1: account { 101: "4899748638", 102: "Jules" }

    def pack_string(field_id, val):
        from core.proto import encode_varint
        data = val.encode()
        tag = (field_id << 3) | 2
        return encode_varint(tag) + encode_varint(len(data)) + data

    inner = pack_string(101, "4899748638") + pack_string(102, "Jules")
    # Wrap in field 1
    from core.proto import encode_varint
    tag1 = (1 << 3) | 2
    outer = encode_varint(tag1) + encode_varint(len(inner)) + inner

    # Add stats (3) -> cs_ranked (304) -> matches (401)
    # cs_ranked inner: 401: 10
    cs_inner = encode_varint((401 << 3) | 0) + encode_varint(10)
    # stats inner: 304: cs_inner
    stats_inner = encode_varint((304 << 3) | 2) + encode_varint(len(cs_inner)) + cs_inner
    # outer stats
    outer += encode_varint((3 << 3) | 2) + encode_varint(len(stats_inner)) + stats_inner

    # Add rank (2) -> battle_royale (201: 104)
    rank_inner = encode_varint((201 << 3) | 0) + encode_varint(104)
    outer += encode_varint((2 << 3) | 2) + encode_varint(len(rank_inner)) + rank_inner

    # Cosmetics (6), Pass (7), Credit (8), Ban (9) - all required by PlayerData
    outer += encode_varint((6 << 3) | 2) + encode_varint(0)
    outer += encode_varint((7 << 3) | 2) + encode_varint(0)
    outer += encode_varint((8 << 3) | 2) + encode_varint(0)
    outer += encode_varint((9 << 3) | 2) + encode_varint(0)

    encrypted = aes_encrypt(outer)

    player_data = decode_player_data(encrypted)
    assert isinstance(player_data, PlayerData)
    assert player_data.account.uid == "4899748638"
    assert player_data.account.nickname == "Jules"
    assert player_data.stats.clash_squad.ranked.matches == 10

def test_rank_translation():
    from config.ranks import get_rank_name
    assert get_rank_name(601) == "Heroic"
    assert get_rank_name(101) == "Bronze I"
    assert get_rank_name(None) == "Unknown"
    assert get_rank_name(999) == "Grandmaster"
