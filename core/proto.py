import struct
import logging
from typing import Any, Dict, List, Optional, Union
from config.fields import REQUEST_FIELD_MAP, RESPONSE_FIELD_MAP

logger = logging.getLogger(__name__)

# Try to import compiled proto classes (Strategy A)
try:
    from proto.compiled import request_pb2, player_pb2
    HAS_COMPILED = hasattr(request_pb2, "PlayerRequest") and hasattr(request_pb2.PlayerRequest, "SerializeToString")
except (ImportError, AttributeError):
    HAS_COMPILED = False
    logger.info("Protoc compiled modules not found. Using raw Strategy B parser.")

# --- Strategy B: Raw Protobuf Parser ---

def encode_varint(value: int) -> bytes:
    """Encodes an integer into a protobuf varint."""
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

def decode_varint(data: bytes, pos: int) -> tuple[int, int]:
    """Decodes a protobuf varint from bytes at a given position."""
    result = 0
    shift = 0
    while True:
        if pos >= len(data):
            raise IndexError("Varint decoding reached end of data")
        b = data[pos]
        result |= (b & 0x7F) << shift
        pos += 1
        if not (b & 0x80):
            break
        shift += 7
    return result, pos

def encode_request_raw(uid: str, region: str, version: str) -> bytes:
    """Encodes a request using raw binary Strategy B."""
    def pack_string(field_id: int, value: str) -> bytes:
        data = value.encode('utf-8')
        tag = (field_id << 3) | 2 # Wire type 2: Length-delimited
        return encode_varint(tag) + encode_varint(len(data)) + data

    return pack_string(1, uid) + pack_string(2, region) + pack_string(3, version)

def decode_response_raw(data: bytes) -> Dict[int, Any]:
    """
    Decodes a response using raw binary Strategy B.
    Recursively decodes identified nested message fields.
    """
    result = {}
    pos = 0

    # Message-type field IDs that should be recursively decoded (Strategy B)
    # 1: account, 2: rank, 3: stats, 4: social, 5: pet, 6: cosmetics, 7: pass, 8: credit, 9: ban
    # 301-304: Stat lines (solo, duo, squad, cs_ranked)
    NESTED_FIELDS = set(range(1, 10)) | set(range(301, 305))

    while pos < len(data):
        try:
            tag, pos = decode_varint(data, pos)
        except (IndexError, ValueError):
            break

        field_id = tag >> 3
        wire_type = tag & 0x07

        val: Any = None
        try:
            if wire_type == 0: # Varint
                val, pos = decode_varint(data, pos)
            elif wire_type == 1: # 64-bit
                if pos + 8 > len(data): break
                val = struct.unpack("<Q", data[pos:pos+8])[0]
                pos += 8
            elif wire_type == 2: # Length-delimited
                length, pos = decode_varint(data, pos)
                if pos + length > len(data): break
                val = data[pos:pos+length]
                pos += length

                # Recursive decoding for identified nested fields
                if field_id in NESTED_FIELDS:
                    try:
                        val = decode_response_raw(val)
                    except Exception:
                        pass # Keep as raw bytes if recursive decoding fails
            elif wire_type == 5: # 32-bit
                if pos + 4 > len(data): break
                val = struct.unpack("<I", data[pos:pos+4])[0]
                pos += 4
            else:
                # Unknown wire type, potentially corrupted or unsupported
                break
        except (IndexError, struct.error):
            break

        if field_id in result:
            # Handle repeated fields by consolidating into a list
            if not isinstance(result[field_id], list):
                result[field_id] = [result[field_id]]
            result[field_id].append(val)
        else:
            result[field_id] = val

    return result

# --- Public API ---

def encode_request(uid: str, region: str, version: str) -> bytes:
    """Entry point for encoding player requests."""
    if HAS_COMPILED:
        try:
            req = request_pb2.PlayerRequest()
            req.uid = uid
            req.region = region
            req.version = version
            return req.SerializeToString()
        except Exception as e:
            logger.warning(f"Strategy A encoding failed: {e}. Falling back to Strategy B.")

    return encode_request_raw(uid, region, version)

def decode_response(data: Union[bytes, Dict[int, Any]]) -> Dict[int, Any]:
    """
    Entry point for decoding player responses.
    Accepts raw bytes or an already decoded dict to maintain consistency.
    """
    if isinstance(data, dict):
        return data
    if not isinstance(data, (bytes, bytearray)) or not data:
        return {}
    return decode_response_raw(bytes(data))
