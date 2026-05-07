import asyncio
import time
from fastapi import APIRouter, Query
from typing import List, Optional
from core.fetcher import fetch_player
from api.schemas import PlayerResponse, PlayerRequest, ResponseMetadata
from api.errors import FFError, ErrorCode
from pydantic import ValidationError
from config.regions import REGION_MAP
from config.settings import settings

router = APIRouter()

async def safe_fetch(uid: str, region: str) -> PlayerResponse:
    """Wrapper to catch exceptions and return a valid PlayerResponse for batch tasks."""
    try:
        # Validate early to catch formatting errors
        # Note: PlayerRequest validation may raise ValidationError for 'fail' as UID
        PlayerRequest(uid=uid, region=region)
        return await fetch_player(uid, region)
    except Exception as exc:
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
            message = exc.errors()[0]["msg"]
            code = ErrorCode.INVALID_UID
            if "region" in message.lower():
                code = ErrorCode.INVALID_REGION

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
            error={
                "code": code,
                "message": message,
                "retryable": retryable,
                "extra": extra
            }
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
