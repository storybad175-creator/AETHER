import struct
from typing import Any, Dict, List
from config.fields import PROTO_FIELD_MAP

# Strategy B: Raw Protobuf Parser (Varint Tag-Length-Value)
class RawProto:
    @staticmethod
    def encode_varint(value: int) -> bytes:
        bits = value & 0x7f
        value >>= 7
        ret = bytes()
        while value:
            ret += struct.pack("B", 0x80 | bits)
            bits = value & 0x7f
            value >>= 7
        ret += struct.pack("B", bits)
        return ret

    @staticmethod
    def decode_varint(data: bytes, pos: int) -> (int, int):
        result = 0
        shift = 0
        while True:
            byte = data[pos]
            result |= (byte & 0x7f) << shift
            pos += 1
            if not (byte & 0x80):
                return result, pos
            shift += 7

    def encode(self, fields: Dict[int, Any]) -> bytes:
        buffer = bytes()
        for field_id, value in fields.items():
            if isinstance(value, int):
                # Wire type 0: Varint
                buffer += self.encode_varint((field_id << 3) | 0)
                buffer += self.encode_varint(value)
            elif isinstance(value, str):
                # Wire type 2: Length-delimited
                encoded_str = value.encode("utf-8")
                buffer += self.encode_varint((field_id << 3) | 2)
                buffer += self.encode_varint(len(encoded_str))
                buffer += encoded_str
            elif isinstance(value, bytes):
                # Wire type 2: Length-delimited
                buffer += self.encode_varint((field_id << 3) | 2)
                buffer += self.encode_varint(len(value))
                buffer += value
        return buffer

    def decode(self, data: bytes) -> Dict[str, Any]:
        result = {}
        pos = 0
        while pos < len(data):
            tag, pos = self.decode_varint(data, pos)
            wire_type = tag & 0x07
            field_id = tag >> 3

            field_name = PROTO_FIELD_MAP.get(field_id, f"field_{field_id}")

            value = None
            if wire_type == 0:  # Varint
                value, pos = self.decode_varint(data, pos)
            elif wire_type == 2:  # Length-delimited
                length, pos = self.decode_varint(data, pos)
                raw_val = data[pos : pos + length]
                pos += length
                try:
                    value = raw_val.decode("utf-8")
                except UnicodeDecodeError:
                    value = raw_val
            else:
                # Skip other wire types for simplicity in raw parser
                pass

            if value is not None:
                if field_name in result:
                    if isinstance(result[field_name], list):
                        result[field_name].append(value)
                    else:
                        result[field_name] = [result[field_name], value]
                else:
                    result[field_name] = value
        return result

raw_proto = RawProto()

# Strategy A detection
HAS_COMPILED_PROTO = False
try:
    from proto.compiled import request_pb2, player_pb2
    if hasattr(request_pb2, "PlayerRequest"):
        HAS_COMPILED_PROTO = True
except ImportError:
    pass

def encode_request(uid: str, region: str) -> bytes:
    if HAS_COMPILED_PROTO:
        req = request_pb2.PlayerRequest()
        req.uid = int(uid)
        req.region = region
        return req.SerializeToString()

    # Fallback to Strategy B
    return raw_proto.encode({1: int(uid), 2: region})

def decode_response(data: bytes) -> Dict[str, Any]:
    # We always use Strategy B for the blackbox decoder to avoid
    # maintaining a massive .proto file for all 60+ fields
    return raw_proto.decode(data)
