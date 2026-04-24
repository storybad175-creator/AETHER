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

from api.schemas import PlayerRequest

@router.get("/batch", response_model=List[PlayerResponse])
async def get_players_batch(
    uids: str = Query(..., description="Comma-separated list of UIDs"),
    region: str = Query(..., description="Region code")
):
    """Fetches multiple players concurrently (max 10)."""
    uid_list = [uid.strip() for uid in uids.split(",") if uid.strip()][:10]

    async def safe_fetch(uid: str, region: str) -> PlayerResponse:
        try:
            # Validate UID before fetching
            PlayerRequest(uid=uid, region=region)
        except ValueError as e:
            from api.errors import ErrorCode
            from api.schemas import ResponseMetadata, ErrorDetail
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
                    code=ErrorCode.INVALID_UID,
                    message=str(e),
                    retryable=False
                )
            )

        try:
            return await fetch_player(uid, region)
        except Exception as e:
            # If fetch_player raises, we wrap it in a PlayerResponse with error
            # Most FFErrors are already caught inside fetch_player and returned as PlayerResponse?
            # Wait, fetch_player raises FFError, it doesn't return it in PlayerResponse on error.
            # Only the middleware converts raised FFErrors to JSON responses.
            # For batch, we want to return a list of responses, some might be errors.
            from api.errors import FFError, ErrorCode
            from api.schemas import ResponseMetadata, ErrorDetail

            error_code = ErrorCode.SERVICE_UNAVAILABLE
            message = str(e)
            retryable = False
            extra = None

            if isinstance(e, FFError):
                error_code = e.code
                message = e.message
                retryable = e.retryable
                extra = e.extra

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
                    code=error_code,
                    message=message,
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
