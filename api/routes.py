import time
import asyncio
from fastapi import APIRouter, Query, Depends
from typing import List
from api.schemas import PlayerResponse, PlayerRequest, ResponseMetadata
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from config.settings import settings

router = APIRouter()
START_TIME = time.time()

@router.get("/player", response_model=PlayerResponse)
async def get_player(
    uid: str = Query(..., description="Player Unique ID"),
    region: str = Query(..., description="Region Code")
):
    """Fetches full player data for a single UID and region."""
    # Validation handled by dependency or Pydantic (if using a model)
    # We explicitly validate here to trigger the middleware handler
    req = PlayerRequest(uid=uid, region=region)
    return await fetch_player(req.uid, req.region)

@router.get("/batch", response_model=List[PlayerResponse])
async def get_batch_players(
    uids: str = Query(..., description="Comma-separated list of UIDs"),
    region: str = Query(..., description="Region Code")
):
    """Fetches player data for up to 10 UIDs concurrently."""
    uid_list = [u.strip() for u in uids.split(",") if u.strip()][:10]

    async def safe_fetch(uid: str):
        try:
            # Validate individual request
            req = PlayerRequest(uid=uid, region=region)
            return await fetch_player(req.uid, req.region)
        except Exception as e:
            # Wrap validation or other errors in a PlayerResponse
            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    response_time_ms=0,
                    api_version=settings.OB_VERSION,
                    cache_hit=False
                ),
                error={
                    "code": "INVALID_UID" if "UID" in str(e) else "SERVICE_UNAVAILABLE",
                    "message": str(e),
                    "retryable": False
                }
            )

    tasks = [safe_fetch(uid) for uid in uid_list]
    return await asyncio.gather(*tasks)

@router.get("/health")
async def health_check():
    """Returns the API health status and uptime."""
    return {
        "status": "ok",
        "ob_version": settings.OB_VERSION,
        "uptime_seconds": int(time.time() - START_TIME),
        "active_regions": len(REGION_MAP)
    }

@router.get("/regions")
async def list_regions():
    """Lists all 14 supported Garena regions."""
    return {
        "count": len(REGION_MAP),
        "regions": list(REGION_MAP.keys())
    }
