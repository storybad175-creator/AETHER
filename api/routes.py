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
    uid: str = Query(..., description="Player UID", min_length=5, max_length=13),
    region: str = Query(..., description="Region code (e.g. IND, SG)")
):
    """Fetches full player data for a given UID and region."""
    return await fetch_player(uid, region)

@router.get("/batch", response_model=List[PlayerResponse])
async def get_players_batch(
    uids: str = Query(..., description="Comma-separated list of UIDs"),
    region: str = Query(..., description="Region code")
):
    """Fetches multiple players concurrently (max 10 UIDs per request)."""
    uid_list = [uid.strip() for uid in uids.split(",") if uid.strip()][:10]
    tasks = [fetch_player(uid, region) for uid in uid_list]
    # return_exceptions=True so that one failing UID doesn't crash the whole batch
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any exceptions that occurred during gather
    final_results = []
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            # In a real production scenario, we'd wrap the exception into a PlayerResponse with error
            # But fetch_player already catches most and returns/raises.
            # If it's a raw Exception here, it was unexpected.
            from api.errors import FFError, ErrorCode
            from api.schemas import ResponseMetadata, ErrorDetail

            error_res = PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid_list[i],
                    request_region=region,
                    fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    response_time_ms=0,
                    api_version=settings.OB_VERSION,
                    cache_hit=False
                ),
                data=None,
                error=ErrorDetail(
                    code=getattr(res, 'code', "INTERNAL_ERROR"),
                    message=str(res),
                    retryable=False
                )
            )
            final_results.append(error_res)
        else:
            final_results.append(res)

    return final_results

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
