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

# Fields identified as nested messages in Garena protocol
NESTED_FIELDS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 301, 302, 303, 304}

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
    Recursive implementation that automatically handles nested messages
    and repeated fields.
    """
    result = {}
    pos = 0
    while pos < len(data):
        try:
            tag, pos = decode_varint(data, pos)
        except (IndexError, struct.error):
            break # Reached end of data or malformed tag

        field_id = tag >> 3
        wire_type = tag & 0x07

        val = None
        try:
            if wire_type == 0: # Varint
                val, pos = decode_varint(data, pos)
            elif wire_type == 1: # 64-bit
                val = struct.unpack("<Q", data[pos:pos+8])[0]
                pos += 8
            elif wire_type == 2: # Length-delimited
                length, pos = decode_varint(data, pos)
                val = data[pos:pos+length]
                pos += length

                # Recursively decode nested messages if identified as such
                if field_id in NESTED_FIELDS and len(val) > 0:
                    try:
                        nested_val = decode_response_raw(val)
                        if nested_val: # Only use if it actually decoded something
                            val = nested_val
                    except Exception:
                        pass # Keep as raw bytes if recursive decode fails
            elif wire_type == 5: # 32-bit
                val = struct.unpack("<I", data[pos:pos+4])[0]
                pos += 4
            else:
                # Unknown wire type, skip or raise? We'll skip for robustness
                logger.debug(f"Unknown wire type {wire_type} for field {field_id}")
                break
        except (IndexError, struct.error):
            break

        # Handle repeated fields by storing them in a list
        if field_id in result:
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

def decode_response(data: bytes) -> Union[Dict[int, Any], bytes]:
    """Entry point for decoding player responses."""
    if not data:
        return {}
    return decode_response_raw(data)
