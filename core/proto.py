import struct
from typing import Any, Dict, List
import logging

from config.fields import PROTO_FIELD_MAP

logger = logging.getLogger(__name__)

try:
    from proto.compiled import request_pb2, player_pb2
    # Check if they are actually compiled classes or just stubs
    STRATEGY_A_AVAILABLE = hasattr(request_pb2, 'PlayerRequest') and hasattr(player_pb2, 'PlayerData')
except ImportError:
    STRATEGY_A_AVAILABLE = False
    logger.info("Protoc compiled classes not found. Falling back to Strategy B (raw binary).")

class ProtobufHandler:
    @staticmethod
    def encode_request(uid: str, region: str) -> bytes:
        if STRATEGY_A_AVAILABLE:
            req = request_pb2.PlayerRequest()
            req.uid = uid
            req.region = region
            return req.SerializeToString()

        # Strategy B: Manual Varint Encoding
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

        # Field 1: UID (string), Field 2: Region (string)
        uid_bytes = uid.encode('utf-8')
        region_bytes = region.encode('utf-8')

        # Tag = (field_number << 3) | wire_type. Wire type 2 = length-delimited.
        res = to_varint((1 << 3) | 2) + to_varint(len(uid_bytes)) + uid_bytes
        res += to_varint((2 << 3) | 2) + to_varint(len(region_bytes)) + region_bytes
        return res

    @staticmethod
    def decode_response(data: bytes) -> Dict[str, Any]:
        # We always use Strategy B for the flexible decoder to map via PROTO_FIELD_MAP
        # unless we want strictly typed objects from Strategy A.
        # Given the "blackbox" requirement, Strategy B is more robust for unknown fields.

        result = {}
        pos = 0
        limit = len(data)

        def read_varint():
            nonlocal pos
            res = 0
            shift = 0
            while True:
                b = data[pos]
                pos += 1
                res |= (b & 0x7f) << shift
                if not (b & 0x80):
                    return res
                shift += 7

        while pos < limit:
            tag = read_varint()
            field_number = tag >> 3
            wire_type = tag & 0x07

            field_name = PROTO_FIELD_MAP.get(field_number, f"unknown_{field_number}")

            if wire_type == 0: # Varint
                val = read_varint()
                result[field_name] = val
            elif wire_type == 1: # 64-bit
                val = struct.unpack("<Q", data[pos:pos+8])[0]
                pos += 8
                result[field_name] = val
            elif wire_type == 2: # Length-delimited
                length = read_varint()
                val_bytes = data[pos:pos+length]
                pos += length
                try:
                    result[field_name] = val_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    # Might be a list of ints or nested message
                    if field_name in ["equipped_outfit_ids", "equipped_weapon_skin_ids"]:
                        # Handle packed repeated fields (simple heuristic)
                        ints = []
                        internal_pos = 0
                        while internal_pos < len(val_bytes):
                            # This is a simplification; assuming varints
                            item_res = 0
                            item_shift = 0
                            while True:
                                item_b = val_bytes[internal_pos]
                                internal_pos += 1
                                item_res |= (item_b & 0x7f) << item_shift
                                if not (item_b & 0x80):
                                    break
                                item_shift += 7
                            ints.append(item_res)
                        result[field_name] = ints
                    else:
                        result[field_name] = list(val_bytes)
            elif wire_type == 5: # 32-bit
                val = struct.unpack("<I", data[pos:pos+4])[0]
                pos += 4
                result[field_name] = val
            else:
                raise ValueError(f"Unsupported wire type: {wire_type}")

        return result

proto_handler = ProtobufHandler()
