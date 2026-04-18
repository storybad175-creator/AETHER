from fastapi import APIRouter, Query, HTTPException
from typing import List
from api.schemas import PlayerResponse, PlayerRequest
from core.fetcher import fetch_player
from config.regions import REGION_MAP
from config.settings import settings
import asyncio
import time

router = APIRouter()

@router.get("/player", response_model=PlayerResponse)
async def get_player(
    uid: str = Query(..., description="Player UID"),
    region: str = Query(..., description="Region code (e.g. IND, BR, SG)")
):
    # Validation is handled by fetch_player calling api/schemas.py validators
    # if we used Pydantic models as input, but here we use Query.
    # So we manually trigger validation.
    PlayerRequest(uid=uid, region=region)
    return await fetch_player(uid, region)

@router.get("/batch", response_model=List[PlayerResponse])
async def get_batch(
    uids: str = Query(..., description="Comma-separated UIDs"),
    region: str = Query(..., description="Region code")
):
    uid_list = [u.strip() for u in uids.split(",") if u.strip()][:10]
    tasks = [fetch_player(uid, region) for uid in uid_list]
    return await asyncio.gather(*tasks)

@router.get("/regions")
async def get_regions():
    return list(REGION_MAP.keys())

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "ob_version": settings.ob_version,
        "uptime": int(time.perf_counter())
    }
