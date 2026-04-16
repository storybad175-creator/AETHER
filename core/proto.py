import struct
import logging
from typing import Any, Dict, List, Optional, Union

# Strategy A: Try to import compiled protobuf classes
try:
    from proto.compiled import player_pb2, request_pb2
    # Verify that the expected classes are actually present
    STRATEGY_A_AVAILABLE = hasattr(player_pb2, 'AccountInfo') and hasattr(request_pb2, 'PlayerRequest')
except (ImportError, TypeError):
    STRATEGY_A_AVAILABLE = False

logger = logging.getLogger(__name__)

class ProtoHandler:
    """Handles Protobuf encoding and decoding using dual strategies."""

    def encode_request(self, uid: str, region: str) -> bytes:
        """Encodes a player data request."""
        if STRATEGY_A_AVAILABLE:
            try:
                req = request_pb2.PlayerRequest()
                req.uid = uid
                req.region = region
                return req.SerializeToString()
            except Exception as e:
                logger.warning(f"Strategy A encoding failed: {e}. Falling back to Strategy B.")

        return self._encode_raw_request(uid, region)

    def decode_response(self, data: bytes) -> Dict[str, Any]:
        """Decodes an encrypted and then decrypted player data response."""
        # Note: Even if Strategy A is available, the response often contains
        # many nested/dynamic fields that Strategy B handles more flexibly
        # for blackbox reverse engineering.
        return self._decode_raw_message(data)

    # ── Strategy B: Raw Binary Implementation (Varint / Tag-Length-Value) ──

    def _encode_varint(self, value: int) -> bytes:
        """Encodes an integer as a protobuf varint."""
        bits = value & 0x7f
        value >>= 7
        ret = bytes()
        while value:
            ret += struct.pack('B', 0x80 | bits)
            bits = value & 0x7f
            value >>= 7
        ret += struct.pack('B', bits)
        return ret

    def _decode_varint(self, data: bytes, pos: int) -> tuple[int, int]:
        """Decodes a protobuf varint from data at pos. Returns (value, new_pos)."""
        res = 0
        shift = 0
        while True:
            b = data[pos]
            res |= (b & 0x7f) << shift
            pos += 1
            if not (b & 0x80):
                return res, pos
            shift += 7
            if shift >= 64:
                raise ValueError("Varint too long")

    def _encode_raw_request(self, uid: str, region: str) -> bytes:
        """Binary encoding for PlayerRequest { 1: uid, 2: region }."""
        # Field 1: string uid (wire type 2: length-delimited)
        # Tag = (field_number << 3) | wire_type = (1 << 3) | 2 = 10 (0x0a)
        res = b'\x0a'
        uid_bytes = uid.encode('utf-8')
        res += self._encode_varint(len(uid_bytes))
        res += uid_bytes

        # Field 2: string region (wire type 2: length-delimited)
        # Tag = (2 << 3) | 2 = 18 (0x12)
        res += b'\x12'
        region_bytes = region.encode('utf-8')
        res += self._encode_varint(len(region_bytes))
        res += region_bytes

        return res

    def _decode_raw_message(self, data: bytes) -> Dict[int, Any]:
        """Generic protobuf message decoder into a field_id -> value map."""
        res: Dict[int, Any] = {}
        pos = 0
        limit = len(data)

        while pos < limit:
            try:
                tag, pos = self._decode_varint(data, pos)
                field_number = tag >> 3
                wire_type = tag & 0x07

                if wire_type == 0:  # Varint
                    val, pos = self._decode_varint(data, pos)
                    self._add_field(res, field_number, val)
                elif wire_type == 1:  # 64-bit
                    val = struct.unpack('<Q', data[pos:pos+8])[0]
                    pos += 8
                    self._add_field(res, field_number, val)
                elif wire_type == 2:  # Length-delimited
                    length, pos = self._decode_varint(data, pos)
                    val = data[pos:pos+length]
                    pos += length
                    self._add_field(res, field_number, val)
                elif wire_type == 5:  # 32-bit
                    val = struct.unpack('<I', data[pos:pos+4])[0]
                    pos += 4
                    self._add_field(res, field_number, val)
                else:
                    # Groups (3, 4) are deprecated/rare in this protocol
                    break
            except (IndexError, ValueError, struct.error):
                break

        return res

    def _add_field(self, res: Dict[int, Any], field_number: int, value: Any):
        """Helper to handle repeated fields by storing them as lists."""
        if field_number in res:
            if isinstance(res[field_number], list):
                res[field_number].append(value)
            else:
                res[field_number] = [res[field_number], value]
        else:
            res[field_number] = value

proto_handler = ProtoHandler()
