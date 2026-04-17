import time
import asyncio
from typing import Optional
from config.settings import settings
from config.regions import REGION_MAP
from core.proto import encode_request
from core.crypto import aes_encrypt
from core.transport import transport
from core.decoder import decode_player_data
from core.cache import cache
from api.schemas import PlayerResponse, ResponseMetadata, ErrorDetail
from api.errors import FFError, ErrorCode

async def fetch_player(uid: str, region: str) -> PlayerResponse:
    start_time = time.monotonic()
    region = region.upper()

    # Check cache first
    cached_data = await cache.get(uid, region)
    if cached_data:
        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                response_time_ms=int((time.monotonic() - start_time) * 1000),
                api_version=settings.OB_VERSION,
                cache_hit=True
            ),
            data=cached_data,
            error=None
        )

    try:
        # Validate region
        if region not in REGION_MAP:
            raise FFError(ErrorCode.INVALID_REGION, f"Unsupported region: {region}")

        url = f"{REGION_MAP[region]}/api/v1/account?region={region}&uid={uid}"

        # Pipeline
        payload_proto = encode_request(uid, region)
        payload_encrypted = aes_encrypt(payload_proto)

        response_encrypted = await transport.post(url, payload_encrypted)
        player_data = decode_player_data(response_encrypted)

        # Cache result
        await cache.set(uid, region, player_data)

        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                response_time_ms=int((time.monotonic() - start_time) * 1000),
                api_version=settings.OB_VERSION,
                cache_hit=False
            ),
            data=player_data,
            error=None
        )

    except FFError as e:
        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                response_time_ms=int((time.monotonic() - start_time) * 1000),
                api_version=settings.OB_VERSION,
                cache_hit=False
            ),
            data=None,
            error=ErrorDetail(
                code=e.code,
                message=e.message,
                retryable=e.retryable,
                extra=e.extra
            )
        )
    except Exception as e:
        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                response_time_ms=int((time.monotonic() - start_time) * 1000),
                api_version=settings.OB_VERSION,
                cache_hit=False
            ),
            data=None,
            error=ErrorDetail(
                code=ErrorCode.SERVICE_UNAVAILABLE,
                message=f"Internal server error: {str(e)}",
                retryable=True,
                extra=None
            )
        )
