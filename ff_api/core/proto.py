import struct
from typing import Any, Dict, List
import logging

from ff_api.config.fields import PROTO_FIELD_MAP

logger = logging.getLogger(__name__)

# Strategy A: Use compiled proto classes if they exist
# In this environment, we intentionally skip Strategy A to use the robust Strategy B implementation
# due to lack of a protoc compiler to generate correct _pb2 files.
HAS_COMPILED_PROTO = False
logger.info("Using raw protobuf parser (Strategy B)")

def encode_varint(value: int) -> bytes:
    """Encodes an integer as a protobuf varint."""
    bits = value & 0x7f
    value >>= 7
    ret = bytearray()
    while value:
        ret.append(0x80 | bits)
        bits = value & 0x7f
        value >>= 7
    ret.append(bits)
    return bytes(ret)

def decode_varint(data: bytes, pos: int) -> (int, int):
    """Decodes a protobuf varint from data starting at pos."""
    res = 0
    shift = 0
    while True:
        b = data[pos]
        res |= (b & 0x7f) << shift
        pos += 1
        if not (b & 0x80):
            return res, pos
        shift += 7

def encode_request(uid: str, region: str) -> bytes:
    """Strategy B fallback for encoding a request."""
    # Wire format for tag 1 (uid): (field_number << 3) | wire_type
    # wire_type for string (length-delimited) is 2.
    uid_bytes = uid.encode("utf-8")
    region_bytes = region.encode("utf-8")

    res = bytearray()
    # Field 1: uid (string)
    res.append((1 << 3) | 2)
    res.extend(encode_varint(len(uid_bytes)))
    res.extend(uid_bytes)

    # Field 2: region (string)
    res.append((2 << 3) | 2)
    res.extend(encode_varint(len(region_bytes)))
    res.extend(region_bytes)

    return bytes(res)

def decode_response(data: bytes) -> Dict[str, Any]:
    """Strategy B fallback for decoding a response using PROTO_FIELD_MAP."""
    res = {}
    pos = 0
    while pos < len(data):
        try:
            tag, pos = decode_varint(data, pos)
            field_num = tag >> 3
            wire_type = tag & 0x07

            field_name = PROTO_FIELD_MAP.get(field_num, f"unknown_{field_num}")

            if wire_type == 0:  # Varint
                val, pos = decode_varint(data, pos)
                res[field_name] = val
            elif wire_type == 2:  # Length-delimited
                length, pos = decode_varint(data, pos)
                val = data[pos:pos+length]
                pos += length

                # Try to decode as UTF-8, else keep as bytes
                try:
                    res[field_name] = val.decode("utf-8")
                except UnicodeDecodeError:
                    res[field_name] = val
            elif wire_type == 1:  # 64-bit
                res[field_name] = struct.unpack("<Q", data[pos:pos+8])[0]
                pos += 8
            elif wire_type == 5:  # 32-bit
                res[field_name] = struct.unpack("<I", data[pos:pos+4])[0]
                pos += 4
            else:
                # Skip unknown wire types if possible, but this is a simplified parser
                raise ValueError(f"Unknown wire type: {wire_type}")
        except Exception as e:
            logger.error(f"Error decoding protobuf at pos {pos}: {e}")
            break

    return res

# If Strategy A is available, we could wrap the compiled classes
# but Strategy B is implemented as requested for the definitive implementation.
