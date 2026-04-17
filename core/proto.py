import struct
from typing import Any, Dict, List
import logging

# Strategy A: Preferred - use compiled proto classes if available
try:
    from proto.compiled import request_pb2, player_pb2
    STRATEGY_A_AVAILABLE = hasattr(request_pb2, 'PlayerRequest')
except ImportError:
    STRATEGY_A_AVAILABLE = False

logger = logging.getLogger(__name__)

if not STRATEGY_A_AVAILABLE:
    logger.info("protoc compiled modules not found — using raw protobuf Strategy B (fallback)")

# Strategy B: Fallback - Raw binary protobuf encode/decode
# Following the Protobuf wire format spec (Tag-Length-Value, Varints)

def encode_varint(value: int) -> bytes:
    """Encodes an integer as a protobuf varint."""
    if value == 0:
        return b'\x00'
    ret = bytearray()
    while value:
        part = value & 0x7F
        value >>= 7
        if value:
            part |= 0x80
        ret.append(part)
    return bytes(ret)

def decode_varint(data: bytes, pos: int) -> (int, int):
    """Decodes a protobuf varint from bytes at pos. Returns (value, next_pos)."""
    res = 0
    shift = 0
    while True:
        b = data[pos]
        res |= (b & 0x7F) << shift
        pos += 1
        if not (b & 0x80):
            return res, pos
        shift += 7

def encode_request(uid: str, region: str) -> bytes:
    """Encodes a player data request."""
    if STRATEGY_A_AVAILABLE:
        req = request_pb2.PlayerRequest()
        req.uid = uid
        req.region = region
        return req.SerializeToString()

    # Strategy B implementation
    # field 1: uid (string)
    # field 2: region (string)
    def encode_field(field_number: int, wire_type: int, value: Any) -> bytes:
        tag = (field_number << 3) | wire_type
        header = encode_varint(tag)
        if wire_type == 2:  # Length-delimited (string, bytes, nested messages)
            content = value.encode('utf-8') if isinstance(value, str) else value
            return header + encode_varint(len(content)) + content
        elif wire_type == 0:  # Varint
            return header + encode_varint(value)
        return b''

    return encode_field(1, 2, uid) + encode_field(2, 2, region)

def decode_response(data: bytes) -> Dict[int, Any]:
    """Decodes a protobuf response into a flat dict of field_id -> value.
    Handles repeated fields by collecting them into a list."""
    # We always use Strategy B for decoding to be flexible with unknown fields
    res = {}
    pos = 0
    limit = len(data)

    def add_field(fn, val):
        if fn in res:
            if isinstance(res[fn], list):
                res[fn].append(val)
            else:
                res[fn] = [res[fn], val]
        else:
            res[fn] = val

    while pos < limit:
        try:
            tag, pos = decode_varint(data, pos)
            field_number = tag >> 3
            wire_type = tag & 0x07

            if wire_type == 0:  # Varint
                value, pos = decode_varint(data, pos)
                add_field(field_number, value)
            elif wire_type == 1:  # 64-bit
                value = struct.unpack('<Q', data[pos:pos+8])[0]
                add_field(field_number, value)
                pos += 8
            elif wire_type == 2:  # Length-delimited
                length, pos = decode_varint(data, pos)
                value = data[pos:pos+length]
                # Try decoding as string, keep as bytes if it fails
                try:
                    decoded_val = value.decode('utf-8')
                except UnicodeDecodeError:
                    decoded_val = value
                add_field(field_number, decoded_val)
                pos += length
            elif wire_type == 5:  # 32-bit
                value = struct.unpack('<I', data[pos:pos+4])[0]
                add_field(field_number, value)
                pos += 4
            else:
                # Unknown wire type, skip
                break
        except Exception:
            break

    return res
