import asyncio
import time
import logging
from fastapi import APIRouter, Query, Request
from typing import List, Optional
from core.fetcher import fetch_player
from api.schemas import PlayerResponse, ResponseMetadata, ErrorDetail, PlayerRequest
from config.regions import REGION_MAP
from config.settings import settings
from api.errors import FFError, ErrorCode
from pydantic import ValidationError

router = APIRouter()
logger = logging.getLogger(__name__)

def create_error_response(uid: str, region: str, exc: Exception) -> PlayerResponse:
    """Helper to standardize error responses within the API."""
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
        code = ErrorCode.INVALID_UID # Or a more general INVALID_INPUT
        message = exc.errors()[0]["msg"]
        retryable = False

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
    """Safely fetches a single player, catching any error to prevent batch failure."""
    try:
        # Pre-validate to ensure we have valid UID/Region for the error response
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
