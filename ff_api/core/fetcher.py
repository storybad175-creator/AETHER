import time
import asyncio
from datetime import datetime, timezone
from ff_api.config.settings import settings
from ff_api.config.regions import REGION_MAP
from ff_api.core.proto import encode_request
from ff_api.core.crypto import aes_encrypt
from ff_api.core.transport import transport
from ff_api.core.decoder import decode_player_data
from ff_api.core.cache import cache
from ff_api.api.schemas import PlayerRequest, PlayerResponse, ResponseMetadata
from ff_api.api.errors import FFError, ErrorCode

async def fetch_player(uid: str, region: str) -> PlayerResponse:
    start_time = time.monotonic()

    # 1. Validation (Pydantic will handle this at the route layer, but for safety)
    region = region.upper()
    if region not in REGION_MAP:
        raise FFError(ErrorCode.INVALID_REGION, f"Unsupported region: {region}")
    if not uid.isdigit() or not (5 <= len(uid) <= 13):
        raise FFError(ErrorCode.INVALID_UID, "UID must be numeric and between 5–13 digits.")

    # 2. Cache Lock (Prevents Cache Stampede)
    lock = await cache.get_lock(uid, region)
    async with lock:
        # 3. Check Cache
        cached_data = cache.get(uid, region)
        if cached_data:
            metadata = ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                response_time_ms=int((time.monotonic() - start_time) * 1000),
                api_version=settings.OB_VERSION,
                cache_hit=True
            )
            return PlayerResponse(metadata=metadata, data=cached_data)

        # 4. Perform Fetch
        try:
            url = f"{REGION_MAP[region]}/api/v1/account" # Simplified example URL

            proto_bytes = encode_request(uid, region)
            encrypted_data = aes_encrypt(proto_bytes)

            resp_bytes = await transport.post(url, encrypted_data, settings.OB_VERSION)
            player_data = decode_player_data(resp_bytes)

            # 5. Store in Cache
            cache.set(uid, region, player_data)

            metadata = ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                response_time_ms=int((time.monotonic() - start_time) * 1000),
                api_version=settings.OB_VERSION,
                cache_hit=False
            )
            return PlayerResponse(metadata=metadata, data=player_data)

        except FFError:
            raise
        except Exception as e:
            raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Internal orchestrator error: {str(e)}")
