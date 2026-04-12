import pytest
from core.crypto import cipher
from core.proto import encode_request, decode_response
from core.decoder import decoder

def test_aes_round_trip():
    data = b"hello world"
    encrypted = cipher.encrypt(data)
    decrypted = cipher.decrypt(encrypted)
    assert decrypted == data

def test_proto_encode_request():
    uid = "123456"
    region = "IND"
    version = "OB53"
    encoded = encode_request(uid, region, version)
    assert isinstance(encoded, bytes)
    assert len(encoded) > 0

def test_rank_translation():
    # 106 is Heroic
    raw_data = {
        "account_info": {"nickname": "Tester", "uid": 123},
        "rank_info": {"br_rank_code": 601}
    }
    decoded = decoder.decode(raw_data)
    assert decoded["rank"]["battle_royale"]["rank_name"] == "Heroic"

def test_missing_optional_fields():
    # Missing stats and pet
    raw_data = {
        "account_info": {"nickname": "Tester", "uid": 123}
    }
    decoded = decoder.decode(raw_data)
    assert decoded["account"]["nickname"] == "Tester"
    assert decoded["pet"] is None
    assert decoded["stats"]["battle_royale"]["solo"]["matches"] == 0
