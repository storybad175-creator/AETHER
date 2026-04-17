import pytest
from core.crypto import aes_encrypt, aes_decrypt
from core.proto import encode_request, decode_response
from core.decoder import decode_player_data

def test_aes_round_trip(mock_settings):
    data = b"hello world 123"
    encrypted = aes_encrypt(data)
    decrypted = aes_decrypt(encrypted)
    assert decrypted == data

def test_proto_encode(mock_settings):
    encoded = encode_request("12345", "IND")
    assert isinstance(encoded, bytes)
    assert len(encoded) > 0

def test_full_decode(mock_settings, mock_encrypted_response):
    player_data = decode_player_data(mock_encrypted_response)
    assert player_data.account.uid == "4899748638"
    assert player_data.account.nickname == "Ƭɴɪᴛᴀᴄʜɪ"

def test_decode_repeated_fields(mock_settings):
    from core.proto import encode_varint
    def pack_field(fn, wt, val):
        tag = (fn << 3) | wt
        if wt == 2:
            content = val.encode('utf-8')
            return encode_varint(tag) + encode_varint(len(content)) + content
        elif wt == 0:
            return encode_varint(tag) + encode_varint(val)
        return b''

    # field 94: equipped_outfit_ids (repeated int32)
    raw_proto = pack_field(94, 0, 1001) + pack_field(94, 0, 1002)
    encrypted = aes_encrypt(raw_proto)
    player_data = decode_player_data(encrypted)
    assert player_data.cosmetics.equipped_outfit_ids == [1001, 1002]

def test_rank_translation():
    from config.ranks import get_rank_name
    assert get_rank_name(601) == "Heroic"
    assert "Unknown" in get_rank_name(9999)
