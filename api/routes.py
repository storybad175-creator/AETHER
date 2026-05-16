import asyncio
import time
import logging
from fastapi import APIRouter, Query
from typing import List, Optional
from core.fetcher import fetch_player
from api.schemas import PlayerResponse, ResponseMetadata, PlayerRequest, ErrorDetail
from config.regions import REGION_MAP
from config.settings import settings
from pydantic import ValidationError

logger = logging.getLogger(__name__)
router = APIRouter()

async def safe_fetch(uid: str, region: str) -> PlayerResponse:
    """Wraps fetch_player to handle exceptions and ensure a PlayerResponse is always returned."""
    start_time = time.monotonic()
    try:
        # Validate first to catch early
        PlayerRequest(uid=uid, region=region)
        return await fetch_player(uid, region)
    except ValidationError as e:
        duration = int((time.monotonic() - start_time) * 1000)
        code = "INVALID_UID" if "uid" in str(e).lower() else "INVALID_REGION"
        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                response_time_ms=duration,
                api_version=settings.OB_VERSION,
                cache_hit=False
            ),
            error=ErrorDetail(
                code=code,
                message=e.errors()[0]["msg"],
                retryable=False
            )
        )
    except Exception as e:
        duration = int((time.monotonic() - start_time) * 1000)
        from api.errors import FFError
        if isinstance(e, FFError):
            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    response_time_ms=duration,
                    api_version=settings.OB_VERSION,
                    cache_hit=False
                ),
                error=ErrorDetail(
                    code=e.code,
                    message=e.message,
                    retryable=e.retryable,
                    extra=e.extra
                )
            )

        logger.exception(f"Unhandled error in safe_fetch for {uid}")
        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                response_time_ms=duration,
                api_version=settings.OB_VERSION,
                cache_hit=False
            ),
            error=ErrorDetail(
                code="SERVICE_UNAVAILABLE",
                message="An unexpected error occurred during batch fetch.",
                retryable=True
            )
        )

@router.get("/player", response_model=PlayerResponse)
async def get_player(
    uid: str = Query(..., description="Player UID"),
    region: str = Query(..., description="Region code (e.g. IND, SG)")
):
    """Fetches full player data for a given UID and region."""
    return await fetch_player(uid, region)

@router.get("/batch", response_model=List[PlayerResponse])
async def get_players_batch(
    uids: str = Query(..., description="Comma-separated list of UIDs"),
    region: str = Query(..., description="Region code")
):
    """Fetches multiple players concurrently (max 10)."""
    uid_list = [uid.strip() for uid in uids.split(",") if uid.strip()][:10]
    tasks = [safe_fetch(uid, region) for uid in uid_list]
    return await asyncio.gather(*tasks)

@router.get("/health")
async def health_check():
    """Returns the API health status and version."""
    return {
        "status": "ok",
        "ob_version": settings.OB_VERSION,
        "api_version": "v3.0-unlimited",
        "timestamp": time.time()
    }

@router.get("/regions")
async def list_regions():
    """Lists all supported Garena regions."""
    return list(REGION_MAP.keys())
