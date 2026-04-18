import time
import asyncio
from typing import Optional
from config.regions import REGION_MAP
from config.settings import settings
from core.crypto import crypto
from core.proto import proto_handler
from core.transport import transport
from core.decoder import decoder
from core.cache import cache
from api.schemas import PlayerResponse, ResponseMetadata, PlayerRequest, ErrorDetail
from api.errors import FFError, ErrorCode

# Per-request locks to prevent cache stampede
_request_locks = {}

async def fetch_player(uid: str, region: str) -> PlayerResponse:
    start_time = time.monotonic()
    region = region.upper()

    # 1. Validation
    if region not in REGION_MAP:
        raise FFError(ErrorCode.INVALID_REGION, f"Region {region} is not supported")

    # 2. Cache Check
    cached_data = await cache.get(uid, region)
    if cached_data:
        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                response_time_ms=int((time.monotonic() - start_time) * 1000),
                api_version=settings.ob_version,
                cache_hit=True
            ),
            data=cached_data,
            error=None
        )

    # 3. Concurrency Lock (Stampede protection)
    lock_key = (uid, region)
    if lock_key not in _request_locks:
        _request_locks[lock_key] = asyncio.Lock()

    async with _request_locks[lock_key]:
        # Double check cache after acquiring lock
        cached_data = await cache.get(uid, region)
        if cached_data:
            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    response_time_ms=int((time.monotonic() - start_time) * 1000),
                    api_version=settings.ob_version,
                    cache_hit=True
                ),
                data=cached_data,
                error=None
            )

        try:
            # 4. Pipeline
            endpoint = f"{REGION_MAP[region]}/api/v1/account" # Example endpoint structure

            # Protobuf Encode
            proto_bytes = proto_handler.encode_request(uid, region)

            # AES Encrypt
            encrypted_payload = crypto.encrypt(proto_bytes)

            # Transport
            encrypted_response = await transport.post(endpoint, encrypted_payload)

            # AES Decrypt
            decrypted_response = crypto.decrypt(encrypted_response)

            # Protobuf Decode
            raw_dict = proto_handler.decode_response(decrypted_response)

            # Map to Schema
            player_data = decoder.decode(raw_dict, region)

            # 5. Cache Set
            await cache.set(uid, region, player_data)

            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    response_time_ms=int((time.monotonic() - start_time) * 1000),
                    api_version=settings.ob_version,
                    cache_hit=False
                ),
                data=player_data,
                error=None
            )

        except FFError:
            raise
        except Exception as e:
            raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Internal fetch error: {str(e)}")
        finally:
            # Cleanup lock
            if lock_key in _request_locks and not _request_locks[lock_key].locked():
                del _request_locks[lock_key]
