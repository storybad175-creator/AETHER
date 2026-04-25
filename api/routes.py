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
    uid: str = Query(..., description="Player UID"),
    region: str = Query(..., description="Region code (e.g. IND, SG)")
):
    """Fetches full player data for a given UID and region."""
    return await fetch_player(uid, region)

@router.get("/batch", response_model=List[PlayerResponse])
async def get_players_batch(
    uids: str = Query(..., description="Comma-separated list of UIDs"),
    region: str = Query(..., description="Region code")
):
    """Fetches multiple players concurrently (max 10)."""
    from api.schemas import PlayerRequest, ResponseMetadata, ErrorDetail
    from api.errors import FFError, ErrorCode

    uid_list = [uid.strip() for uid in uids.split(",") if uid.strip()][:10]

    async def safe_fetch(uid: str, region: str) -> PlayerResponse:
        try:
            # Re-validate individually to catch format errors per UID
            PlayerRequest(uid=uid, region=region)
            return await fetch_player(uid, region)
        except Exception as e:
            code = ErrorCode.SERVICE_UNAVAILABLE
            retryable = True
            extra = None
            if isinstance(e, FFError):
                code = e.code
                retryable = e.retryable
                extra = e.extra
            elif isinstance(e, ValueError):
                code = ErrorCode.INVALID_UID
                retryable = False

            return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    response_time_ms=0,
                    api_version=settings.OB_VERSION,
                    cache_hit=False
                ),
                data=None,
                error=ErrorDetail(
                    code=code,
                    message=str(e),
                    retryable=retryable,
                    extra=extra
                )
            )

    tasks = [safe_fetch(uid, region) for uid in uid_list]
    return await asyncio.gather(*tasks)

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
