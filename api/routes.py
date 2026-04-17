import time
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from api.schemas import PlayerResponse, PlayerRequest
from core.fetcher import fetch_player
from config.settings import settings
from config.regions import REGION_MAP

router = APIRouter()

@router.get("/player", response_model=PlayerResponse)
async def get_player(
    uid: str = Query(..., description="The player's UID"),
    region: str = Query(..., description="The player's region")
):
    # Validation is handled by Pydantic if we used a model,
    # but for GET params we do it manually or via Depends
    try:
        # Trigger validation
        PlayerRequest(uid=uid, region=region)
    except ValueError as e:
        from api.errors import FFError, ErrorCode
        raise FFError(ErrorCode.INVALID_UID if "UID" in str(e) else ErrorCode.INVALID_REGION, str(e))

    return await fetch_player(uid, region)

@router.get("/batch", response_model=List[PlayerResponse])
async def get_player_batch(
    uids: str = Query(..., description="Comma-separated UIDs"),
    region: str = Query(..., description="The region for all UIDs")
):
    uid_list = [u.strip() for u in uids.split(",") if u.strip()][:10]
    tasks = [fetch_player(uid, region) for uid in uid_list]
    results = await asyncio.gather(*tasks)
    return results

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "ob_version": settings.OB_VERSION,
        "uptime_seconds": int(time.perf_counter())
    }

@router.get("/regions")
async def list_regions():
    return list(REGION_MAP.keys())
