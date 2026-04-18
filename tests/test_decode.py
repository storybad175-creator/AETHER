import pytest
from core.crypto import crypto
from core.proto import proto_handler
from core.decoder import decoder

def test_aes_round_trip(mock_settings):
    original_data = b"Hello Protobuf"
    encrypted = crypto.encrypt(original_data)
    assert encrypted != original_data
    decrypted = crypto.decrypt(encrypted)
    assert decrypted == original_data

def test_proto_encode(mock_settings):
    uid = "12345678"
    region = "IND"
    encoded = proto_handler.encode_request(uid, region)
    assert isinstance(encoded, bytes)
    assert len(encoded) > 0

def test_full_decode(mock_settings, mock_raw_player_dict, sample_region):
    player_data = decoder.decode(mock_raw_player_dict, sample_region)
    assert player_data.account.uid == "4899748638"
    assert player_data.account.nickname == "TestPlayer"
    assert player_data.rank.battle_royale.rank_name == "Platinum IV"
    assert player_data.stats.battle_royale.solo.win_rate == "10.00%"
    assert player_data.stats.battle_royale.solo.kd_ratio == 3.33 # 300 / 90
    assert player_data.ban.is_banned is False

def test_missing_optional_fields(mock_settings, sample_region):
    # Only minimal account data
    minimal_dict = {
        "account": {"uid": "12345", "nickname": "Noob"},
        "rank": {},
        "stats": {},
        "cosmetics": {},
        "pass_info": {},
        "credit": {},
        "ban": {}
    }
    player_data = decoder.decode(minimal_dict, sample_region)
    assert player_data.account.uid == "12345"
    assert player_data.social.guild is None
    assert player_data.pet is None
