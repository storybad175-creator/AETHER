import asyncio
import time
from fastapi import APIRouter, Query
from typing import List, Optional
from core.fetcher import fetch_player
from api.schemas import PlayerResponse
from config.regions import REGION_MAP
from config.settings import settings

router = APIRouter()

@router.get("/player", response_model=PlayerResponse)
async def get_player(
    uid: str = Query(..., description="Player UID (5-13 digits)"),
    region: str = Query(..., description="Region code (IND, BR, SG, RU, ID, TW, US, VN, TH, ME, PK, CIS, BD, NA)")
):
    """
    Fetches comprehensive player profile and stats for a given UID and Region.
    """
    return await fetch_player(uid, region)

@router.get("/batch", response_model=List[PlayerResponse])
async def get_players_batch(
    uids: str = Query(..., description="Comma-separated list of UIDs"),
    region: str = Query(..., description="Region code")
):
    """
    Fetches up to 10 players concurrently.
    Errors for individual UIDs are returned as PlayerResponse objects with error details.
    """
    uid_list = [u.strip() for u in uids.split(",") if u.strip()][:10]

    # Run all fetches concurrently
    results = await asyncio.gather(
        *[fetch_player(uid, region) for uid in uid_list],
        return_exceptions=True
    )

    final_responses = []
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            # Convert exceptions to PlayerResponse with error metadata
            from api.errors import FFError
            uid = uid_list[i]
            error_code = res.code if isinstance(res, FFError) else "SERVICE_UNAVAILABLE"
            error_msg = str(res)

            final_responses.append(PlayerResponse(
                metadata={
                    "request_uid": uid,
                    "request_region": region,
                    "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    "response_time_ms": 0,
                    "api_version": settings.OB_VERSION,
                    "cache_hit": False
                },
                error={
                    "code": error_code,
                    "message": error_msg,
                    "retryable": getattr(res, 'retryable', False)
                }
            ))
        else:
            final_responses.append(res)

    return final_responses

@router.get("/health")
async def health_check():
    """Returns the API health status, current OB version, and uptime."""
    return {
        "status": "ok",
        "ob_version": settings.OB_VERSION,
        "api_version": "v3.0-unlimited",
        "timestamp": time.time()
    }

@router.get("/regions")
async def list_regions():
    """Lists all 14 supported Garena regions."""
    return list(REGION_MAP.keys())
