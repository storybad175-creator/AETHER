import asyncio
from typing import List
from fastapi import APIRouter, Query, HTTPException
from api.schemas import PlayerResponse, PlayerRequest
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from api.errors import FFError, ErrorCode

router = APIRouter()

@router.get("/player", response_model=PlayerResponse)
async def get_player(uid: str = Query(...), region: str = Query(...)):
    try:
        # Validate through Pydantic
        req = PlayerRequest(uid=uid, region=region)
        return await fetch_player(req.uid, req.region)
    except ValueError as e:
        # Pydantic validation error
        raise FFError(ErrorCode.INVALID_UID if "UID" in str(e) else ErrorCode.INVALID_REGION, str(e))

@router.get("/batch", response_model=List[PlayerResponse])
async def get_batch(uids: str = Query(...), region: str = Query(...)):
    uid_list = [u.strip() for u in uids.split(",")]
    if len(uid_list) > 10:
        raise FFError(ErrorCode.INVALID_UID, "Batch limited to 10 UIDs.")

    tasks = [fetch_player(uid, region) for uid in uid_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    final_results = []
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            # Map exception to PlayerResponse with error
            final_results.append(PlayerResponse(
                metadata=None, # Or build basic metadata
                data=None,
                error={"code": "FETCH_FAILED", "message": str(res), "retryable": True}
            ))
        else:
            final_results.append(res)

    return final_results

@router.get("/health")
async def health_check():
    return {"status": "ok", "ob_version": "OB53", "uptime": 0} # Uptime would need a global tracker

@router.get("/regions")
async def list_regions():
    return list(REGION_MAP.keys())
