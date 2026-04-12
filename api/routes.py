import asyncio
from fastapi import APIRouter, Query, Request
from api.schemas import PlayerResponse, PlayerRequest
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from config.settings import settings
from typing import List

router = APIRouter()

@router.get("/player", response_model=PlayerResponse)
async def get_player(
    uid: str = Query(..., description="The player's UID"),
    region: str = Query(..., description="The player's region (e.g., IND, BR, SG)")
):
    """Fetches full player data for a given UID and region."""
    # Validation is handled within fetch_player and via Pydantic if we used a body,
    # but for GET params we do it in fetch_player.
    result = await fetch_player(uid, region)
    return result

@router.get("/batch", response_model=List[PlayerResponse])
async def get_batch_players(
    uids: str = Query(..., description="Comma-separated list of UIDs"),
    region: str = Query(..., description="The region for all UIDs")
):
    """Fetches data for multiple UIDs (up to 10) concurrently."""
    uid_list = [uid.strip() for uid in uids.split(",") if uid.strip()][:10]
    tasks = [fetch_player(uid, region) for uid in uid_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    final_results = []
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            # Convert exception to a PlayerResponse error shape
            from api.errors import FFError, ErrorCode
            if isinstance(res, FFError):
                err_res = {
                    "metadata": {
                        "request_uid": uid_list[i],
                        "request_region": region,
                        "fetched_at": "",
                        "response_time_ms": 0,
                        "api_version": settings.OB_VERSION,
                        "cache_hit": False
                    },
                    "data": None,
                    "error": {
                        "code": res.code,
                        "message": res.message,
                        "retryable": res.retryable,
                        "extra": res.extra
                    }
                }
            else:
                err_res = {
                    "metadata": {
                        "request_uid": uid_list[i],
                        "request_region": region,
                        "fetched_at": "",
                        "response_time_ms": 0,
                        "api_version": settings.OB_VERSION,
                        "cache_hit": False
                    },
                    "data": None,
                    "error": {
                        "code": ErrorCode.SERVICE_UNAVAILABLE,
                        "message": str(res),
                        "retryable": False,
                        "extra": None
                    }
                }
            final_results.append(err_res)
        else:
            final_results.append(res)

    return final_results

@router.get("/health")
async def health_check():
    """Returns the API health status and version."""
    return {
        "status": "ok",
        "ob_version": settings.OB_VERSION,
        "supported_regions": list(REGION_MAP.keys())
    }

@router.get("/regions")
async def list_regions():
    """Lists all 14 supported Garena regions."""
    return list(REGION_MAP.keys())
