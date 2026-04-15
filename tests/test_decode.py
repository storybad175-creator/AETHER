import pytest
from core.crypto import cipher
from core.proto import encode_request, decode_response
from core.decoder import map_to_player_data, decode_payload

def test_aes_round_trip():
    original = b"Hello, Free Fire API!"
    encrypted = cipher.encrypt(original)
    decrypted = cipher.decrypt(encrypted)
    assert decrypted == original

def test_proto_encode():
    encoded = encode_request("12345", "IND")
    assert isinstance(encoded, bytes)
    assert len(encoded) > 0

def test_map_to_player_data():
    raw = {
        "uid": 12345,
        "nickname": "Player1",
        "level": 50,
        "br_rank_code": 101,
        "br_solo_matches": 10,
        "br_solo_wins": 2
    }
    data = map_to_player_data(raw)
    assert data["account"]["nickname"] == "Player1"
    assert data["rank"]["battle_royale"]["rank_name"] == "Bronze I"
    assert data["stats"]["battle_royale"]["solo"]["win_rate"] == "20.00%"
