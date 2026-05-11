import asyncio
import time
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from core.fetcher import fetch_player
from api.schemas import PlayerResponse, PlayerRequest
from config.regions import list_regions
from config.settings import settings
from api.errors import FFError, ErrorCode
from pydantic import ValidationError

router = APIRouter()

def create_error_response(uid: str, region: str, exc: Exception) -> PlayerResponse:
    """Helper to create a PlayerResponse from an exception."""
    if isinstance(exc, FFError):
        return PlayerResponse(
            metadata={
                "request_uid": uid,
                "request_region": region,
                "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                "response_time_ms": 0,
                "api_version": settings.OB_VERSION,
                "cache_hit": False
            },
            data=None,
            error={
                "code": exc.code,
                "message": exc.message,
                "retryable": exc.retryable,
                "extra": exc.extra
            }
        )
    return PlayerResponse(
        metadata={
            "request_uid": uid,
            "request_region": region,
            "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "response_time_ms": 0,
            "api_version": settings.OB_VERSION,
            "cache_hit": False
        },
        data=None,
        error={
            "code": ErrorCode.SERVICE_UNAVAILABLE,
            "message": str(exc),
            "retryable": False
        }
    )

@router.get("/player", response_model=PlayerResponse)
async def get_player(
    uid: str = Query(..., description="Player UID"),
    region: str = Query(..., description="Region code (e.g. IND, SG)")
):
    """Fetches full player data for a given UID and region."""
    # Validation is handled by middleware catching ValidationError
    PlayerRequest(uid=uid, region=region)
    return await fetch_player(uid, region)

@router.get("/batch", response_model=List[PlayerResponse])
async def get_players_batch(
    uids: str = Query(..., description="Comma-separated list of UIDs"),
    region: str = Query(..., description="Region code")
):
    """Fetches multiple players concurrently (max 10)."""
    uid_list = [uid.strip() for uid in uids.split(",") if uid.strip()][:10]

    async def safe_fetch(uid: str, region: str):
        try:
            PlayerRequest(uid=uid, region=region)
            return await fetch_player(uid, region)
        except ValidationError as e:
            msg = e.errors()[0]["msg"]
            code = ErrorCode.INVALID_UID if "UID" in msg else ErrorCode.INVALID_REGION
            return create_error_response(uid, region, FFError(code, msg))
        except Exception as e:
            return create_error_response(uid, region, e)

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
async def regions():
    """Lists all supported Garena regions."""
    return list_regions()
