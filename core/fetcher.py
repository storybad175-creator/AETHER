import time
from typing import Dict, Any, List
from core.transport import transport
from core.crypto import cipher
from core.proto import encode_request, decode_response
from core.decoder import decoder
from core.cache import cache
from config.settings import settings
from config.regions import REGION_MAP
from api.errors import FFError, ErrorCode

async def fetch_player(uid: str, region: str) -> Dict[str, Any]:
    """Orchestrates the full fetch pipeline for a single player."""
    start_time = time.monotonic()
    region = region.upper()

    if region not in REGION_MAP:
        raise FFError(ErrorCode.INVALID_REGION, f"Region '{region}' is not supported.")

    if not uid.isdigit() or not (5 <= len(uid) <= 13):
        raise FFError(ErrorCode.INVALID_UID, "UID must be numeric and between 5–13 digits.")

    # 1. Check Cache
    cached_data = await cache.get(uid, region)
    if cached_data:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        cached_data["metadata"]["response_time_ms"] = duration_ms
        cached_data["metadata"]["cache_hit"] = True
        return cached_data

    # 2. Build URL
    base_url = REGION_MAP[region]
    url = f"{base_url}/api/v1/account?region={region}&uid={uid}"

    try:
        # 3. Encode Request
        proto_req = encode_request(uid, region, settings.OB_VERSION)

        # 4. Encrypt Request
        encrypted_req = cipher.encrypt(proto_req)

        # 5. Transport
        encrypted_resp = await transport.post(url, encrypted_req)

        # 6. Decrypt Response
        try:
            decrypted_resp = cipher.decrypt(encrypted_resp)
        except Exception:
            raise FFError(ErrorCode.DECODE_ERROR, "Failed to decrypt response. AES keys might be outdated.", extra={"possible_key_rotation": True})

        # 7. Decode Protobuf
        try:
            raw_dict = decode_response(decrypted_resp)
        except Exception as e:
            raise FFError(ErrorCode.DECODE_ERROR, f"Failed to decode protobuf: {str(e)}")

        # 8. Structure Data
        player_data = decoder.decode(raw_dict)

        if not player_data.get("account", {}).get("nickname"):
            raise FFError(ErrorCode.PLAYER_NOT_FOUND, f"Player with UID {uid} not found in region {region}.")

        duration_ms = int((time.monotonic() - start_time) * 1000)

        response = {
            "metadata": {
                "request_uid": uid,
                "request_region": region,
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "response_time_ms": duration_ms,
                "api_version": settings.OB_VERSION,
                "cache_hit": False
            },
            "data": player_data,
            "error": None
        }

        # 9. Cache Result
        await cache.set(uid, region, response)

        return response

    except FFError:
        raise
    except Exception as e:
        raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"An unexpected error occurred: {str(e)}")
