from __future__ import annotations
import asyncio
import time
from fastapi import APIRouter, Query
from typing import List, Optional
from core.fetcher import fetch_player
from api.schemas import PlayerResponse, PlayerRequest
from config.regions import REGION_MAP
from config.settings import settings
from api.errors import FFError, ErrorCode

router = APIRouter()

async def safe_fetch(uid: str, region: str) -> PlayerResponse:
    """Helper to fetch player while catching and wrapping errors into PlayerResponse."""
    try:
        # Pre-validate to catch formatting errors early
        PlayerRequest(uid=uid, region=region)
        return await fetch_player(uid, region)
    except FFError as e:
        return PlayerResponse(
            metadata={
                "request_uid": uid,
                "request_region": region,
                "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                "response_time_ms": 0,
                "api_version": settings.OB_VERSION,
                "cache_hit": False
            },
            error={
                "code": e.code,
                "message": e.message,
                "retryable": e.retryable,
                "extra": e.extra
            }
        )
    except Exception:
        return PlayerResponse(
            metadata={
                "request_uid": uid,
                "request_region": region,
                "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                "response_time_ms": 0,
                "api_version": settings.OB_VERSION,
                "cache_hit": False
            },
            error={
                "code": ErrorCode.SERVICE_UNAVAILABLE,
                "message": "An unexpected error occurred during batch fetch.",
                "retryable": False
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
