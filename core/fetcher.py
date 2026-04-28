import time
import logging
from typing import Optional
from config.settings import settings
from config.regions import get_region_url
from core.proto import encode_request
from core.crypto import aes_encrypt
from core.transport import transport
from core.decoder import decode_player_data
from core.cache import cache
from api.schemas import PlayerResponse, ResponseMetadata, PlayerRequest
from api.errors import FFError, ErrorCode

logger = logging.getLogger(__name__)

async def fetch_player(uid: str, region: str) -> PlayerResponse:
    """
    High-level orchestrator to fetch player data.
    Handles validation, caching, encryption, network, and decoding.
    """
    start_time = time.monotonic()

    # Normalize input
    uid = str(uid).strip()
    region = region.upper().strip()

    # 1. Validation (Indirectly via PlayerRequest Pydantic model)
    try:
        PlayerRequest(uid=uid, region=region)
    except Exception as e:
        # Wrap validation errors into FFError
        raise FFError(ErrorCode.INVALID_UID if "UID" in str(e) else ErrorCode.INVALID_REGION, str(e))

    # 2. Cache Check (Immediate return on hit)
    cached_data = cache.get(uid, region)
    if cached_data:
        duration = int((time.monotonic() - start_time) * 1000)
        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                response_time_ms=duration,
                api_version=settings.OB_VERSION,
                cache_hit=True
            ),
            data=cached_data
        )

    # 3. Lock per UID/Region to prevent cache stampede
    lock = await cache.get_lock(uid, region)
    async with lock:
        # Re-check cache after acquiring lock
        cached_data = cache.get(uid, region)
        if cached_data:
            duration = int((time.monotonic() - start_time) * 1000)
            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    response_time_ms=duration,
                    api_version=settings.OB_VERSION,
                    cache_hit=True
                ),
                data=cached_data
            )

        try:
            # 4. Build Request
            url = f"{get_region_url(region)}/api/v1/account"

            # 5. Encode & Encrypt
            proto_bytes = encode_request(uid, region, settings.OB_VERSION)
            encrypted_request = aes_encrypt(proto_bytes)

            # 6. Network Transport
            raw_response = await transport.post(url, encrypted_request)

            # 7. Decrypt & Decode
            player_data = decode_player_data(raw_response)

            # 8. Update Cache
            cache.set(uid, region, player_data)

            duration = int((time.monotonic() - start_time) * 1000)
            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    response_time_ms=duration,
                    api_version=settings.OB_VERSION,
                    cache_hit=False
                ),
                data=player_data
            )

        except FFError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error fetching player {uid} ({region})")
            raise FFError(
                ErrorCode.SERVICE_UNAVAILABLE,
                f"An unexpected internal error occurred: {str(e)}"
            )
