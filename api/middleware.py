import time
import uuid
import logging
from datetime import datetime, timezone
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from api.errors import FFError, ERROR_HTTP_MAP, ErrorCode
from api.schemas import PlayerResponse, ErrorDetail, ResponseMetadata
from config.settings import settings

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.request_counts: Dict[str, List[float]] = defaultdict(list)
        self.rpm_limit = settings.RATE_LIMIT_RPM

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean up old requests
        self.request_counts[client_ip] = [t for t in self.request_counts[client_ip] if now - t < 60]

        if len(self.request_counts[client_ip]) >= self.rpm_limit:
            retry_after = 60 - (now - self.request_counts[client_ip][0])
            return JSONResponse(
                status_code=429,
                content={
                    "metadata": {
                        "request_uid": request.query_params.get("uid", "unknown"),
                        "request_region": request.query_params.get("region", "unknown"),
                        "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "response_time_ms": 0,
                        "api_version": settings.OB_VERSION,
                        "cache_hit": False
                    },
                    "data": None,
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": f"Too many requests. Try again in {int(retry_after)}s",
                        "retryable": True,
                        "extra": {"retry_after_seconds": int(retry_after)}
                    }
                },
                headers={"Retry-After": str(int(retry_after))}
            )

        self.request_counts[client_ip].append(now)
        return await call_next(request)

async def error_handler_middleware(request: Request, call_next):
    # Log the incoming request to help debug 401s in tests
    # logger.debug(f"Middleware handling {request.method} {request.url}")
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        from pydantic import ValidationError
        if isinstance(exc, FFError):
            error = exc
        elif isinstance(exc, ValidationError):
            error = FFError(
                ErrorCode.INVALID_UID, # Default for validation errors in this context
                str(exc.errors()[0]["msg"]) if exc.errors() else "Validation Error"
            )
        else:
            logger.exception("Unhandled exception in API")
            error = FFError(
                ErrorCode.SERVICE_UNAVAILABLE,
                f"Internal server error: {str(exc)}"
            )

        status_code = ERROR_HTTP_MAP.get(error.code, 500)

        # Build a consistent response
        from datetime import datetime, timezone
        metadata = ResponseMetadata(
            request_uid=request.query_params.get("uid", "unknown"),
            request_region=request.query_params.get("region", "unknown"),
            fetched_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            response_time_ms=0,
            api_version=settings.OB_VERSION,
            cache_hit=False
        )

        content = PlayerResponse(
            metadata=metadata,
            data=None,
            error=ErrorDetail(
                code=error.code,
                message=error.message,
                retryable=error.retryable,
                extra=error.extra
            )
        ).model_dump()

        return JSONResponse(status_code=status_code, content=content)
