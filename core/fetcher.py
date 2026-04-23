import time
import logging
import asyncio
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
    High-level orchestrator that coordinates the entire fetch pipeline:
    Validation -> Caching -> Protobuf Encoding -> AES Encryption ->
    Network Transport -> AES Decryption -> Protobuf Decoding ->
    Schema Mapping -> Cache Update.
    """
    start_time = time.monotonic()

    # 1. Input Normalization & Validation
    try:
        validated = PlayerRequest(uid=uid, region=region)
        uid = validated.uid
        region = validated.region
    except ValueError as e:
        # Re-raise as FFError for consistent API error handling
        raise FFError(ErrorCode.INVALID_UID, str(e))

    # 2. TTL Cache Check (Fast path)
    cached_data = cache.get(uid, region)
    if cached_data:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                response_time_ms=duration_ms,
                api_version=settings.OB_VERSION,
                cache_hit=True
            ),
            data=cached_data
        )

    # 3. Concurrent Request Protection (Locking)
    # FM-11: Prevent cache stampede for the same UID/Region
    lock = await cache.get_lock(uid, region)
    async with lock:
        # Check cache again inside the lock
        cached_data = cache.get(uid, region)
        if cached_data:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    response_time_ms=duration_ms,
                    api_version=settings.OB_VERSION,
                    cache_hit=True
                ),
                data=cached_data
            )

        try:
            # 4. Pipeline Execution
            url = f"{get_region_url(region)}/api/v1/account"

            # Step A: Encode to Protobuf
            proto_payload = encode_request(uid, region, settings.OB_VERSION)

            # Step B: AES Encrypt
            encrypted_payload = aes_encrypt(proto_payload)

            # Step C: Network POST
            encrypted_response = await transport.post(url, encrypted_payload)

            # Step D: AES Decrypt + Protobuf Decode + Mapping
            player_data = decode_player_data(encrypted_response)

            # 5. Update Cache
            cache.set(uid, region, player_data)

            duration_ms = int((time.monotonic() - start_time) * 1000)
            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    response_time_ms=duration_ms,
                    api_version=settings.OB_VERSION,
                    cache_hit=False
                ),
                data=player_data
            )

        except FFError:
            # Pass through typed errors (404, 401, 429, etc.)
            raise
        except Exception as e:
            # Fallback for unexpected failures (FM-12, FM-03, etc.)
            logger.exception(f"Fetcher encountered unexpected error for {uid} [{region}]")
            raise FFError(
                ErrorCode.SERVICE_UNAVAILABLE,
                f"The verification pipeline failed: {str(e)}"
            )
