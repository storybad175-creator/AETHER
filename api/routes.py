import asyncio
import time
from fastapi import APIRouter, Query
from typing import List, Optional
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from config.settings import settings

from api.schemas import PlayerResponse, ResponseMetadata, ErrorDetail, PlayerRequest
from api.errors import FFError, ErrorCode
from pydantic import ValidationError

router = APIRouter()

def create_error_response(uid: str, region: str, exc: Exception) -> PlayerResponse:
    """Helper to standardize error responses for individual batch tasks."""
    code = ErrorCode.SERVICE_UNAVAILABLE
    message = str(exc)
    retryable = False
    extra = None

    if isinstance(exc, FFError):
        code = exc.code
        message = exc.message
        retryable = exc.retryable
        extra = exc.extra
    elif isinstance(exc, ValidationError):
        errors = exc.errors()
        field = errors[0]["loc"][-1] if errors else ""
        code = ErrorCode.INVALID_UID if field == "uid" else \
               ErrorCode.INVALID_REGION if field == "region" else "INVALID_INPUT"
        message = errors[0]["msg"] if errors else "Invalid input."

    return PlayerResponse(
        metadata=ResponseMetadata(
            request_uid=uid,
            request_region=region,
            fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            response_time_ms=0,
            api_version=settings.OB_VERSION,
            cache_hit=False
        ),
        data=None,
        error=ErrorDetail(
            code=code,
            message=message,
            retryable=retryable,
            extra=extra
        )
    )

async def safe_fetch(uid: str, region: str) -> PlayerResponse:
    """Wraps fetch_player to ensure individual task failures don't crash asyncio.gather."""
    try:
        # Validate before fetching to catch formatting errors early
        PlayerRequest(uid=uid, region=region)
        return await fetch_player(uid, region)
    except Exception as e:
        return create_error_response(uid, region, e)

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
