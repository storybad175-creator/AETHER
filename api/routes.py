import asyncio
import time
import logging
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from core.fetcher import fetch_player
from api.schemas import PlayerResponse, PlayerRequest, ResponseMetadata, ErrorDetail
from api.errors import FFError, ErrorCode
from config.regions import REGION_MAP
from config.settings import settings
from pydantic import ValidationError

router = APIRouter()
logger = logging.getLogger(__name__)

def create_error_response(uid: str, region: str, error: Exception) -> PlayerResponse:
    """Standardizes error responses for batch tasks."""
    code = ErrorCode.SERVICE_UNAVAILABLE
    message = str(error)
    retryable = False
    extra = None

    if isinstance(error, FFError):
        code = error.code
        message = error.message
        retryable = error.retryable
        extra = error.extra
    elif isinstance(error, ValidationError):
        code = ErrorCode.INVALID_UID # Simplification
        message = error.errors()[0]["msg"]

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
    """Wraps fetch_player to ensure it never raises in a batch."""
    try:
        # Pre-validate to catch obvious errors early
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
