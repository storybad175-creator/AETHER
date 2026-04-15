import asyncio
from typing import List
from fastapi import APIRouter, Query, HTTPException
from api.schemas import PlayerResponse, PlayerRequest
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from config.settings import settings
from api.errors import FFError, ErrorCode

router = APIRouter()

@router.get("/player", response_model=PlayerResponse)
async def get_player(
    uid: str = Query(..., description="Player UID"),
    region: str = Query(..., description="Region code (e.g., IND, BR)")
):
    try:
        # Pydantic validation via PlayerRequest
        req = PlayerRequest(uid=uid, region=region)
        return await fetch_player(req.uid, req.region)
    except ValueError as e:
        raise FFError(ErrorCode.INVALID_UID, str(e))

@router.get("/batch", response_model=List[PlayerResponse])
async def get_batch(
    uids: str = Query(..., description="Comma-separated UIDs"),
    region: str = Query(..., description="Region code")
):
    uid_list = [u.strip() for u in uids.split(",") if u.strip()][:10]
    tasks = [fetch_player(uid, region) for uid in uid_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    final_results = []
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            # Wrap exception in a PlayerResponse if possible
            final_results.append({
                "metadata": {"request_uid": uid_list[i], "request_region": region, "api_version": settings.OB_VERSION, "cache_hit": False, "fetched_at": "", "response_time_ms": 0},
                "data": None,
                "error": {"code": "BATCH_ERROR", "message": str(res), "retryable": False}
            })
        else:
            final_results.append(res)
    return final_results

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "ob_version": settings.OB_VERSION,
        "supported_regions": list(REGION_MAP.keys())
    }

@router.get("/regions")
async def get_regions():
    return list(REGION_MAP.keys())
