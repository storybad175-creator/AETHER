import time
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, Tuple
from config.settings import settings
from config.regions import REGION_MAP
from core.proto import encode_request
from core.crypto import aes_encrypt
from core.transport import transport
from core.decoder import decode_player_data
from core.cache import cache
from api.schemas import PlayerResponse, ResponseMetadata, PlayerRequest
from api.errors import FFError, ErrorCode

logger = logging.getLogger(__name__)

# Semaphores to limit total concurrent requests to Garena
_gate = asyncio.Semaphore(10)

# In-memory locks to prevent cache stampedes for the same UID
_locks: dict[Tuple[str, str], asyncio.Lock] = {}

async def fetch_player(uid: str, region: str) -> PlayerResponse:
    """
    The orchestrator coroutine that fetches player data from Garena.
    Handles validation, caching, encryption, transport, and decoding.
    """
    start_time = time.monotonic()
    request_key = (uid, region)

    # 1. Validation (Indirectly handled by PlayerRequest schema if called from API)
    # Ensure normalization
    region = region.upper()
    uid = str(uid)

    # 2. Cache Stampede Prevention & Locking
    if request_key not in _locks:
        _locks[request_key] = asyncio.Lock()

    async with _locks[request_key]:
        # 3. Check Cache
        cached_data = cache.get(uid, region)
        if cached_data:
            return _build_response(uid, region, cached_data, start_time, cache_hit=True)

        # 4. Fetch from Garena
        try:
            async with _gate:
                data = await _execute_fetch(uid, region)

            # 5. Store in Cache
            cache.set(uid, region, data)

            return _build_response(uid, region, data, start_time, cache_hit=False)

        except FFError as e:
            return _build_error_response(uid, region, e, start_time)
        except Exception as e:
            logger.exception(f"Unexpected error fetching player {uid} ({region})")
            return _build_error_response(
                uid, region,
                FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Internal error: {str(e)}"),
                start_time
            )
        finally:
            # Cleanup locks to prevent memory leak
            # We only remove if no one else is waiting
            if not _locks[request_key].locked():
                _locks.pop(request_key, None)

async def _execute_fetch(uid: str, region: str):
    """Internal helper to execute the network pipeline."""
    # Build URL
    base_url = REGION_MAP.get(region)
    if not base_url:
        raise FFError(ErrorCode.INVALID_REGION, f"Region {region} not supported.")

    url = f"{base_url}/api/v1/account" # Example endpoint

    # Encode request
    raw_payload = encode_request(uid, region, settings.OB_VERSION)

    # AES Encrypt
    encrypted_payload = aes_encrypt(raw_payload)

    # Transport (Post)
    # Note: url might need query params depending on exact OB53 spec
    target_url = f"{url}?region={region}&uid={uid}"
    encrypted_response = await transport.post(target_url, encrypted_payload)

    # Decode response
    player_data = decode_player_data(encrypted_response)

    return player_data

def _build_response(uid: str, region: str, data, start_time: float, cache_hit: bool) -> PlayerResponse:
    metadata = ResponseMetadata(
        request_uid=uid,
        request_region=region,
        fetched_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        response_time_ms=int((time.monotonic() - start_time) * 1000),
        api_version=settings.OB_VERSION,
        cache_hit=cache_hit
    )
    return PlayerResponse(metadata=metadata, data=data)

def _build_error_response(uid: str, region: str, error: FFError, start_time: float) -> PlayerResponse:
    metadata = ResponseMetadata(
        request_uid=uid,
        request_region=region,
        fetched_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        response_time_ms=int((time.monotonic() - start_time) * 1000),
        api_version=settings.OB_VERSION,
        cache_hit=False
    )
    return PlayerResponse(
        metadata=metadata,
        error={
            "code": error.code,
            "message": error.message,
            "retryable": error.retryable,
            "extra": error.extra
        }
    )
