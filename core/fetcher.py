import time
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional

from config.settings import settings
from config.regions import REGION_MAP
from core.proto import proto_handler
from core.crypto import aes_cipher
from core.transport import transport
from core.decoder import response_decoder
from core.cache import cache
from api.schemas import PlayerResponse, PlayerData, ResponseMetadata
from api.errors import FFError, ErrorCode

logger = logging.getLogger(__name__)

async def fetch_player(uid: str, region: str) -> PlayerResponse:
    """Orchestrates the full pipeline to fetch and decode player data."""
    start_time = time.monotonic()
    region = region.upper()

    # 1. Validation (Already done by Pydantic if called via FastAPI)
    if region not in REGION_MAP:
        raise FFError(ErrorCode.INVALID_REGION, f"Unsupported region: {region}")

    # 2. Cache Check
    cached_data = await cache.get(uid, region)
    if cached_data:
        return _build_response(uid, region, cached_data, start_time, cache_hit=True)

    # 3. Request Preparation
    url = f"{REGION_MAP[region]}/api/v1/account" # Simplified pattern for this implementation

    try:
        # Step A: Protobuf Encode
        proto_bytes = proto_handler.encode_request(uid, region)

        # Step B: AES Encrypt
        encrypted_req = aes_cipher.encrypt(proto_bytes)

        # Step C: Transport
        encrypted_res = await transport.post(url, encrypted_req)

        # Step D: AES Decrypt
        try:
            decrypted_res = aes_cipher.decrypt(encrypted_res)
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise FFError(
                ErrorCode.DECODE_ERROR,
                "Failed to decrypt Garena response. AES key might be rotated.",
                extra={"possible_key_rotation": True}
            )

        # Step E: Protobuf Decode
        raw_proto = proto_handler.decode_response(decrypted_res)
        if not raw_proto:
            raise FFError(ErrorCode.PLAYER_NOT_FOUND, "Garena returned an empty or unparseable response")

        # Step F: Map to Model
        player_data = response_decoder.decode(raw_proto)

        # 4. Cache Store
        await cache.set(uid, region, player_data)

        return _build_response(uid, region, player_data, start_time, cache_hit=False)

    except FFError as e:
        raise e
    except Exception as e:
        logger.exception(f"Unexpected error fetching player {uid} in {region}")
        raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"An unexpected system error occurred: {str(e)}")

def _build_response(
    uid: str,
    region: str,
    data: Optional[PlayerData],
    start_time: float,
    cache_hit: bool
) -> PlayerResponse:
    duration_ms = int((time.monotonic() - start_time) * 1000)

    metadata = ResponseMetadata(
        request_uid=uid,
        request_region=region,
        fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        response_time_ms=duration_ms,
        api_version=settings.OB_VERSION,
        cache_hit=cache_hit
    )

    return PlayerResponse(
        metadata=metadata,
        data=data,
        error=None
    )
