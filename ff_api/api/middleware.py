import time
import uuid
from typing import Dict, Tuple, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ff_api.api.errors import FFError, ErrorCode, ERROR_HTTP_MAP
from ff_api.api.schemas import PlayerResponse, ResponseMetadata, ErrorDetail
from ff_api.config.settings import settings
from fastapi.responses import JSONResponse
from datetime import datetime, timezone

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rpm_limit: int):
        super().__init__(app)
        self.rpm_limit = rpm_limit
        self.requests: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()

        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Filter requests in the last 60 seconds
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < 60]

        if len(self.requests[client_ip]) >= self.rpm_limit:
            retry_after = 60 - (now - self.requests[client_ip][0])
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Too many requests. Please try again later.",
                        "retryable": True,
                        "extra": {"retry_after_seconds": int(retry_after)}
                    }
                },
                headers={"Retry-After": str(int(retry_after))}
            )

        self.requests[client_ip].append(now)
        return await call_next(request)

async def error_handler_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except FFError as e:
        status_code = ERROR_HTTP_MAP.get(e.code, 500)
        metadata = ResponseMetadata(
            request_uid=request.query_params.get("uid", "unknown"),
            request_region=request.query_params.get("region", "unknown"),
            fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            response_time_ms=0,
            api_version=settings.OB_VERSION,
            cache_hit=False
        )
        error_detail = ErrorDetail(
            code=e.code.value,
            message=e.message,
            retryable=e.retryable,
            extra=e.extra
        )
        return JSONResponse(
            status_code=status_code,
            content=PlayerResponse(metadata=metadata, error=error_detail).model_dump(by_alias=True)
        )
    except Exception as e:
        # Unexpected error
        metadata = ResponseMetadata(
            request_uid=request.query_params.get("uid", "unknown"),
            request_region=request.query_params.get("region", "unknown"),
            fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            response_time_ms=0,
            api_version=settings.OB_VERSION,
            cache_hit=False
        )
        error_detail = ErrorDetail(
            code=ErrorCode.SERVICE_UNAVAILABLE.value,
            message=f"An unexpected error occurred: {str(e)}",
            retryable=False
        )
        return JSONResponse(
            status_code=500,
            content=PlayerResponse(metadata=metadata, error=error_detail).model_dump(by_alias=True)
        )
