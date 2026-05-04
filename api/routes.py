import asyncio
import time
import logging
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from core.fetcher import fetch_player
from api.schemas import PlayerResponse, ResponseMetadata, PlayerRequest, ErrorDetail
from config.regions import REGION_MAP
from config.settings import settings
from api.errors import FFError, ErrorCode
from pydantic import ValidationError

router = APIRouter()
logger = logging.getLogger(__name__)

async def safe_fetch(uid: str, region: str) -> PlayerResponse:
    """Wrapper for fetch_player to handle per-UID errors in batch processing."""
    try:
        # Validate first to catch common errors before network
        try:
            PlayerRequest(uid=uid, region=region)
        except ValidationError as e:
             return PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid=uid,
                    request_region=region,
                    fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    response_time_ms=0,
                    api_version=settings.OB_VERSION,
                    cache_hit=False
                ),
                error=ErrorDetail(
                    code=ErrorCode.INVALID_UID if "UID" in str(e) else ErrorCode.INVALID_REGION,
                    message=e.errors()[0]["msg"],
                    retryable=False
                )
            )

        return await fetch_player(uid, region)
    except FFError as e:
        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                response_time_ms=0,
                api_version=settings.OB_VERSION,
                cache_hit=False
            ),
            error=ErrorDetail(
                code=e.code,
                message=e.message,
                retryable=e.retryable,
                extra=e.extra
            )
        )
    except Exception as e:
        logger.exception(f"Unexpected error in safe_fetch for {uid}")
        return PlayerResponse(
            metadata=ResponseMetadata(
                request_uid=uid,
                request_region=region,
                fetched_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                response_time_ms=0,
                api_version=settings.OB_VERSION,
                cache_hit=False
            ),
            error=ErrorDetail(
                code=ErrorCode.SERVICE_UNAVAILABLE,
                message=f"Internal error: {str(e)}",
                retryable=False
            )
        )

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
    """Fetches multiple players concurrently (max 10). Returns list of responses (some may be errors)."""
    uid_list = [uid.strip() for uid in uids.split(",") if uid.strip()][:10]

    # Process concurrently
    tasks = [safe_fetch(uid, region) for uid in uid_list]
    results = await asyncio.gather(*tasks)

    return list(results)

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
