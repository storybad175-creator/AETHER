import asyncio
import time
from fastapi import APIRouter, Query, Request, Depends
from typing import List, Optional
from api.schemas import PlayerResponse, PlayerRequest
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from config.settings import settings

router = APIRouter()

@router.get("/player", response_model=PlayerResponse)
async def get_player(req: PlayerRequest = Depends()):
    return await fetch_player(req.uid, req.region)

@router.get("/batch", response_model=List[PlayerResponse])
async def get_batch_players(
    uids: str = Query(..., description="Comma-separated UIDs"),
    region: str = Query(..., description="The region code")
):
    # Quick validation for region
    if region.upper() not in REGION_MAP:
        from api.errors import FFError, ErrorCode
        raise FFError(ErrorCode.INVALID_REGION, f"Invalid region: {region}")

    uid_list = [u.strip() for u in uids.split(",") if u.strip()]
    uid_list = uid_list[:10]  # Cap at 10

    tasks = [fetch_player(uid, region) for uid in uid_list]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    final_results = []
    for res in raw_results:
        if isinstance(res, Exception):
            from api.errors import FFError, ErrorCode, ErrorDetail
            from api.schemas import ResponseMetadata
            from datetime import datetime, timezone

            error_obj = res if isinstance(res, FFError) else FFError(ErrorCode.SERVICE_UNAVAILABLE, str(res))
            final_results.append(PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid="unknown", # We don't have it easily here without more mapping
                    request_region=region,
                    fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    response_time_ms=0,
                    api_version=settings.OB_VERSION,
                    cache_hit=False
                ),
                data=None,
                error=ErrorDetail(
                    code=error_obj.code,
                    message=error_obj.message,
                    retryable=error_obj.retryable
                )
            ))
        else:
            final_results.append(res)

    return final_results

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "ob_version": settings.OB_VERSION,
        "timestamp": time.time()
    }

@router.get("/regions")
async def get_supported_regions():
    return list(REGION_MAP.keys())
