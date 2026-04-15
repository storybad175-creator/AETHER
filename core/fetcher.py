import time
from datetime import datetime
from typing import Optional
from config.settings import settings
from config.regions import REGION_MAP
from core.crypto import cipher
from core.proto import encode_request
from core.transport import transport
from core.decoder import decode_payload, map_to_player_data
from core.cache import cache
from api.errors import FFError, ErrorCode

async def fetch_player(uid: str, region: str) -> dict:
    start_time = time.monotonic()
    region = region.upper()

    if region not in REGION_MAP:
        raise FFError(ErrorCode.INVALID_REGION, f"Region {region} is not supported.")

    # 1. Check Cache
    cached_data = await cache.get(uid, region)
    if cached_data:
        response_time = int((time.monotonic() - start_time) * 1000)
        return _wrap_response(uid, region, cached_data, response_time, cache_hit=True)

    # 2. Prepare Request
    endpoint = f"{REGION_MAP[region]}/api/v1/account"
    proto_bytes = encode_request(uid, region)
    encrypted_request = cipher.encrypt(proto_bytes)

    # 3. Network Call
    encrypted_response = await transport.post(endpoint, encrypted_request)

    # 4. Decode & Map
    raw_dict = decode_payload(encrypted_response)
    player_data = map_to_player_data(raw_dict)

    # 5. Store in Cache
    await cache.set(uid, region, player_data)

    response_time = int((time.monotonic() - start_time) * 1000)
    return _wrap_response(uid, region, player_data, response_time, cache_hit=False)

def _wrap_response(uid: str, region: str, data: dict, response_time: int, cache_hit: bool) -> dict:
    return {
        "metadata": {
            "request_uid": uid,
            "request_region": region,
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "response_time_ms": response_time,
            "api_version": settings.OB_VERSION,
            "cache_hit": cache_hit
        },
        "data": data,
        "error": None
    }
