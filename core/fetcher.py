import time
from datetime import datetime, timezone
from core.proto import proto_handler
from core.crypto import cipher
from core.transport import transport
from core.decoder import decoder
from core.cache import cache
from config.regions import REGION_MAP
from api.schemas import PlayerResponse, ResponseMetadata, PlayerRequest
from api.errors import FFError, ErrorCode

async def fetch_player(uid: str, region: str) -> PlayerResponse:
    start_time = time.monotonic()
    region = region.upper()

    # 1. Validation (handled by caller typically, but safe check)
    if region not in REGION_MAP:
        raise FFError(ErrorCode.INVALID_REGION, f"Region {region} not supported.")

    # 2. Cache Check
    cached_data = cache.get(uid, region)
    if cached_data:
        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                response_time_ms=int((time.monotonic() - start_time) * 1000),
                api_version="OB53",
                cache_hit=True
            ),
            data=cached_data,
            error=None
        )

    # 3. Request Pipeline
    lock = await cache.get_lock(uid, region)
    async with lock:
        # Check cache again inside lock (prevent stampede)
        cached_data = cache.get(uid, region)
        if cached_data:
            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    response_time_ms=int((time.monotonic() - start_time) * 1000),
                    api_version="OB53",
                    cache_hit=True
                ),
                data=cached_data,
                error=None
            )

        try:
            url = f"{REGION_MAP[region]}/api/v1/account"

            # Encode
            proto_bytes = proto_handler.encode_request(uid, region)

            # Encrypt
            encrypted_payload = cipher.encrypt(proto_bytes)

            # POST
            encrypted_response = await transport.post(url, encrypted_payload)

            # Decode & Map
            player_data = decoder.decode(encrypted_response)

            # Cache
            cache.set(uid, region, player_data)

            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    response_time_ms=int((time.monotonic() - start_time) * 1000),
                    api_version="OB53",
                    cache_hit=False
                ),
                data=player_data,
                error=None
            )
        except FFError:
            raise
        except Exception as e:
            raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Internal fetcher error: {str(e)}")
