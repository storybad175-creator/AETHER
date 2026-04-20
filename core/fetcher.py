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

    # 1. Validation (Indirectly via PlayerRequest Pydantic model)
    try:
        req = PlayerRequest(uid=uid, region=region)
        uid = req.uid
        region = req.region
    except Exception as e:
        # Pydantic validation errors are handled by middleware in FastAPI,
        # but for CLI/direct calls, we raise them as INVALID_UID/REGION if appropriate.
        raise

    # 2. Cache Check
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

    # 3. Lock per UID/Region to prevent stampede
    lock = await cache.get_lock(uid, region)
    async with lock:
        # Check again in case another coroutine filled it while we waited
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
            try:
                raw_response = await transport.post(url, encrypted_request)
            except FFError as e:
                if e.code == ErrorCode.PLAYER_NOT_FOUND:
                    e.message += " Player may exist in another region. Try: SG, IND, BR, ID."
                raise e

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
                f"An unexpected error occurred: {str(e)}"
            )
