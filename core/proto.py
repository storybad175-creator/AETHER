import struct
from typing import Any, Dict, List, Optional, Union
import logging

from config.fields import PROTO_FIELD_MAP

logger = logging.getLogger(__name__)

# Try to import compiled protos
try:
    from proto.compiled import request_pb2, player_pb2
    HAS_COMPILED = hasattr(request_pb2, "PlayerRequest") # Double check it's not a stub
except (ImportError, AttributeError):
    HAS_COMPILED = False
    logger.info("Compiled protobufs not found or incomplete. Using Strategy B (Raw Binary).")

class ProtobufHandler:
    """
    Handles Protobuf encoding and decoding.
    Strategy A: Uses compiled _pb2.py files if available.
    Strategy B: Raw binary varint-based implementation (Fallback).
    """

    def encode_request(self, uid: str, region: str) -> bytes:
        if HAS_COMPILED:
            req = request_pb2.PlayerRequest()
            req.uid = uid
            req.region = region
            return req.SerializeToString()
        else:
            # Strategy B: Manual Varint Encoding
            # Field 1: uid (string), Field 2: region (string)
            data = self._encode_field(1, 2, uid.encode()) # wire_type 2 = length-delimited
            data += self._encode_field(2, 2, region.encode())
            return data

    def decode_response(self, data: bytes) -> Dict[str, Any]:
        if HAS_COMPILED:
            res = player_pb2.PlayerData()
            res.ParseFromString(data)
            return self._proto_to_dict(res)
        else:
            # Strategy B: Raw binary decode
            return self._decode_raw(data, "response")

    def _encode_field(self, field_number: int, wire_type: int, value: bytes) -> bytes:
        tag = (field_number << 3) | wire_type
        return self._encode_varint(tag) + self._encode_varint(len(value)) + value

    def _encode_varint(self, value: int) -> bytes:
        bits = value & 0x7f
        value >>= 7
        res = bytearray()
        while value:
            res.append(0x80 | bits)
            bits = value & 0x7f
            value >>= 7
        res.append(bits)
        return bytes(res)

    def _decode_varint(self, data: bytes, pos: int) -> (int, int):
        res = 0
        shift = 0
        while True:
            b = data[pos]
            res |= (b & 0x7f) << shift
            pos += 1
            if not (b & 0x80):
                return res, pos
            shift += 7

    def _decode_raw(self, data: bytes, map_name: str) -> Dict[str, Any]:
        res = {}
        pos = 0
        field_map = PROTO_FIELD_MAP.get(map_name, {})

        while pos < len(data):
            try:
                tag, pos = self._decode_varint(data, pos)
                field_number = tag >> 3
                wire_type = tag & 0x07
                field_name = field_map.get(field_number, f"field_{field_number}")

                if wire_type == 0: # Varint
                    val, pos = self._decode_varint(data, pos)
                    res[field_name] = val
                elif wire_type == 2: # Length-delimited
                    length, pos = self._decode_varint(data, pos)
                    val = data[pos:pos+length]
                    pos += length

                    # Heuristic: if field_name maps to another message, recurse
                    if field_name in PROTO_FIELD_MAP:
                         res[field_name] = self._decode_raw(val, field_name)
                    else:
                        try:
                            res[field_name] = val.decode('utf-8')
                        except UnicodeDecodeError:
                            res[field_name] = val
                elif wire_type == 1: # 64-bit
                    res[field_name] = struct.unpack("<Q", data[pos:pos+8])[0]
                    pos += 8
                elif wire_type == 5: # 32-bit
                    res[field_name] = struct.unpack("<I", data[pos:pos+4])[0]
                    pos += 4
                else:
                    # Skip unknown wire types
                    break
            except Exception:
                break

        # Consolidation: if multiple fields with same name (repeated), make list
        # Strategy B simplified: just return the dict
        return res

    def _proto_to_dict(self, obj) -> Dict[str, Any]:
        """Converts compiled proto object to dict recursively."""
        from google.protobuf.json_format import MessageToDict
        return MessageToDict(obj, preserving_proto_field_name=True, use_integers_for_enums=True)

proto_handler = ProtobufHandler()
