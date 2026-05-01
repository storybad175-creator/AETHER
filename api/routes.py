import asyncio
import time
from fastapi import APIRouter, Query
from typing import List, Optional
from core.fetcher import fetch_player
from api.schemas import PlayerResponse, ResponseMetadata, ErrorDetail, PlayerRequest
from config.regions import REGION_MAP
from config.settings import settings
from api.errors import FFError, ErrorCode
from pydantic import ValidationError

router = APIRouter()

async def safe_fetch(uid: str, region: str) -> PlayerResponse:
    """Wraps fetch_player to catch errors and return them as PlayerResponse."""
    try:
        # Explicit validation here for batch individual items
        PlayerRequest(uid=uid, region=region)
        return await fetch_player(uid, region)
    except ValidationError as e:
        error_code = ErrorCode.SERVICE_UNAVAILABLE
        loc = [err.get("loc", []) for err in e.errors()]
        if any("uid" in l for l in loc): error_code = ErrorCode.INVALID_UID
        elif any("region" in l for l in loc): error_code = ErrorCode.INVALID_REGION

        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                response_time_ms=0,
                api_version=settings.OB_VERSION,
                cache_hit=False
            ),
            error=ErrorDetail(
                code=error_code,
                message=e.errors()[0]["msg"],
                retryable=False
            )
        )
    except FFError as e:
        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                response_time_ms=0,
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
    except Exception as e:
        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                response_time_ms=0,
                api_version=settings.OB_VERSION,
                cache_hit=False
            ),
            error=ErrorDetail(
                code=ErrorCode.SERVICE_UNAVAILABLE,
                message=str(e),
                retryable=False
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
