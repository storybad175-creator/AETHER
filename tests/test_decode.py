import pytest
from core.proto import proto_handler
from core.crypto import aes_cipher
from core.decoder import response_decoder

def test_aes_round_trip():
    data = b"hello world 123456"
    encrypted = aes_cipher.encrypt(data)
    decrypted = aes_cipher.decrypt(encrypted)
    assert decrypted == data

def test_proto_encode_request():
    uid = "12345678"
    region = "IND"
    encoded = proto_handler.encode_request(uid, region)
    assert isinstance(encoded, bytes)
    assert len(encoded) > 0

def test_proto_decode_raw():
    # Field 1: Varint 123
    # Tag = (1 << 3) | 0 = 8
    data = b'\x08\x7b'
    decoded = proto_handler.decode_response(data)
    assert decoded[1] == 123

def test_decoder_mapping(sample_uid, sample_region):
    # Mock raw proto dict
    raw_proto = {
        1: { # Account Info
            1: sample_uid,
            2: "Nickname",
            3: 50,
            5: sample_region
        },
        2: { # Rank
            1: 404, # Platinum IV
            2: 2500
        },
        3: {}, # BR Stats
        4: {}, # CS Stats
        5: {}, # Guild
        7: {}, # Cosmetics
        8: {}, # Pass
        9: {}, # Credit
        10: {} # Ban
    }

    player_data = response_decoder.decode(raw_proto)
    assert player_data.account.uid == sample_uid
    assert player_data.account.nickname == "Nickname"
    assert player_data.rank.battle_royale.rank_name == "Platinum IV"
