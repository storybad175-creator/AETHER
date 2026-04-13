import pytest
from ff_api.core.proto import encode_request, decode_response
from ff_api.core.crypto import aes_encrypt, aes_decrypt
from ff_api.core.decoder import decode_player_data

def test_proto_encode():
    data = encode_request("12345", "IND")
    assert isinstance(data, bytes)
    assert len(data) > 0

def test_aes_round_trip():
    original = b"hello world"
    encrypted = aes_encrypt(original)
    decrypted = aes_decrypt(encrypted)
    assert decrypted == original

def test_full_decode(mock_player_raw_dict):
    # This is a bit complex as Strategy B is manual.
    # Let's mock the decode_response to return our dict.
    from unittest.mock import patch
    with patch("ff_api.core.decoder.aes_decrypt", return_value=b"decrypted"):
        with patch("ff_api.core.decoder.decode_response", return_value=mock_player_raw_dict):
            player_data = decode_player_data(b"encrypted")
            assert player_data.account.uid == str(mock_player_raw_dict["uid"])
            assert player_data.account.nickname == mock_player_raw_dict["nickname"]
            assert player_data.rank.battle_royale.rank_code == mock_player_raw_dict["br_rank_code"]
