import pytest
from core.crypto import cipher
from core.proto import proto_handler
from core.decoder import decoder

def test_aes_round_trip():
    data = b"hello world"
    encrypted = cipher.encrypt(data)
    decrypted = cipher.decrypt(encrypted)
    assert decrypted == data

def test_proto_encode():
    encoded = proto_handler.encode_request("12345", "IND")
    assert isinstance(encoded, bytes)
    assert len(encoded) > 0

def test_full_decode():
    # Construct a minimal valid encrypted protobuf response
    # We'll use Strategy B to encode a 'PlayerData' like structure
    def to_varint(n: int) -> bytes:
        buf = bytearray()
        while True:
            towrite = n & 0x7f
            n >>= 7
            if n:
                buf.append(towrite | 0x80)
            else:
                buf.append(towrite)
                break
        return bytes(buf)

    uid_bytes = b"4899748638"
    proto_data = to_varint((1 << 3) | 2) + to_varint(len(uid_bytes)) + uid_bytes

    encrypted = cipher.encrypt(proto_data)
    player_data = decoder.decode(encrypted)

    assert player_data.account.uid == "4899748638"
