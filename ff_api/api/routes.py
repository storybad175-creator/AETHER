import asyncio
import time
from fastapi import APIRouter, Query, Depends
from typing import List
from ff_api.core.fetcher import fetch_player
from ff_api.api.schemas import PlayerResponse, PlayerRequest
from ff_api.config.regions import REGION_MAP
from ff_api.config.settings import settings

router = APIRouter()

@router.get("/player", response_model=PlayerResponse)
async def get_player(uid: str = Query(..., min_length=5, max_length=13), region: str = Query(...)):
    # Pydantic validation is already done by FastAPI if we used a model,
    # but here we use Query for simplicity in the endpoint signature.
    # The fetcher also validates.
    return await fetch_player(uid, region)

from ff_api.api.errors import FFError, ErrorCode
from ff_api.api.schemas import ErrorDetail, ResponseMetadata
from datetime import datetime, timezone

@router.get("/batch", response_model=List[PlayerResponse])
async def get_batch(uids: str = Query(...), region: str = Query(...)):
    uid_list = [uid.strip() for uid in uids.split(",")][:10] # Limit to 10
    tasks = [fetch_player(uid, region) for uid in uid_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    final_results = []
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            # Convert exception to PlayerResponse with error
            error_code = ErrorCode.SERVICE_UNAVAILABLE
            if isinstance(res, FFError):
                error_code = res.code

            error_detail = ErrorDetail(
                code=error_code.value,
                message=str(res),
                retryable=getattr(res, 'retryable', False)
            )
            metadata = ResponseMetadata(
                request_uid=uid_list[i],
                request_region=region,
                fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                response_time_ms=0,
                api_version=settings.OB_VERSION,
                cache_hit=False
            )
            final_results.append(PlayerResponse(metadata=metadata, error=error_detail))
        else:
            final_results.append(res)
    return final_results

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "ob_version": settings.OB_VERSION,
        "uptime": int(time.time()) # This would ideally be calculated from start time
    }

@router.get("/regions")
async def get_regions():
    return list(REGION_MAP.keys())
