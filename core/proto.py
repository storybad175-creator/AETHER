import struct
from typing import Any, Dict, Optional
from config.fields import PROTO_FIELD_MAP, REQUEST_FIELD_MAP

# Strategy A: Compiled Proto (to be implemented in proto/compiled/)
try:
    from proto.compiled import request_pb2, player_pb2
    HAS_COMPILED = True
except ImportError:
    HAS_COMPILED = False

class ProtobufStrategyB:
    """Raw binary Protobuf encode/decode using tag-length-value varint encoding."""

    @staticmethod
    def _encode_varint(value: int) -> bytes:
        """Encodes an integer as a protobuf varint."""
        result = bytearray()
        while True:
            bits = value & 0x7F
            value >>= 7
            if value:
                result.append(bits | 0x80)
            else:
                result.append(bits)
                break
        return bytes(result)

    @staticmethod
    def _decode_varint(data: bytes, pos: int) -> (int, int):
        """Decodes a protobuf varint from bytes at position pos."""
        result = 0
        shift = 0
        while True:
            byte = data[pos]
            result |= (byte & 0x7F) << shift
            pos += 1
            if not (byte & 0x80):
                break
            shift += 7
        return result, pos

    def encode_request(self, uid: str, region: str, version: str) -> bytes:
        """Encodes the request message: field 1 (uid), 2 (region), 3 (version)."""
        # All fields are strings (wire type 2: length-delimited)
        def encode_string(field_number: int, value: str) -> bytes:
            tag = (field_number << 3) | 2
            data = value.encode('utf-8')
            return self._encode_varint(tag) + self._encode_varint(len(data)) + data

        body = (
            encode_string(1, uid) +
            encode_string(2, region) +
            encode_string(3, version)
        )
        return body

    def decode_response(self, data: bytes) -> Dict[str, Any]:
        """Decodes the player response message recursively."""
        return self._decode_message(data, 0, len(data))

    def _decode_message(self, data: bytes, pos: int, end: int) -> Dict[str, Any]:
        result = {}
        while pos < end:
            tag, pos = self._decode_varint(data, pos)
            field_number = tag >> 3
            wire_type = tag & 0x07
            field_name = PROTO_FIELD_MAP.get(field_number, f"field_{field_number}")

            if wire_type == 0:  # Varint
                val, pos = self._decode_varint(data, pos)
                result[field_name] = val
            elif wire_type == 1:  # 64-bit
                val = struct.unpack("<Q", data[pos:pos+8])[0]
                result[field_name] = val
                pos += 8
            elif wire_type == 2:  # Length-delimited
                length, pos = self._decode_varint(data, pos)
                field_data = data[pos:pos+length]
                pos += length

                # Heuristic: try to decode as a nested message if field_name implies it
                if field_name.endswith("_info") or field_name.endswith("_stats"):
                    result[field_name] = self._decode_message(field_data, 0, len(field_data))
                else:
                    try:
                        result[field_name] = field_data.decode('utf-8')
                    except UnicodeDecodeError:
                        result[field_name] = list(field_data) # Treat as bytes/list of ints
            elif wire_type == 5:  # 32-bit
                val = struct.unpack("<I", data[pos:pos+4])[0]
                result[field_name] = val
                pos += 4
            else:
                # Unknown wire type, skip or raise
                raise ValueError(f"Unknown wire type {wire_type} at pos {pos}")
        return result

def encode_request(uid: str, region: str, version: str) -> bytes:
    if HAS_COMPILED:
        req = request_pb2.PlayerRequest()
        req.uid = uid
        req.region = region
        req.version = version
        return req.SerializeToString()
    return ProtobufStrategyB().encode_request(uid, region, version)

def decode_response(data: bytes) -> Dict[str, Any]:
    # For simplicity and robustness, we prefer Strategy B for decoding
    # as it's more flexible with unknown/blackbox fields
    return ProtobufStrategyB().decode_response(data)
