import time
import uuid
import logging
import asyncio
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError
from api.errors import FFError, ErrorCode, ERROR_HTTP_MAP
from config.settings import settings

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Injects a unique X-Request-ID into every response."""
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Implements a simple sliding-window rate limit per client IP.
    Default: 30 requests per minute (RPM).
    """
    def __init__(self, app):
        super().__init__(app)
        self.history: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

        # Start background cleanup task
        self._cleanup_task = None

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        async with self._lock:
            # Lazy start cleanup task
            if self._cleanup_task is None:
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())

            # Initialize or clean history for this IP
            if client_ip not in self.history:
                self.history[client_ip] = []

            # Remove timestamps older than 60 seconds
            self.history[client_ip] = [t for t in self.history[client_ip] if now - t < 60]

            if len(self.history[client_ip]) >= settings.RATE_LIMIT_RPM:
                retry_after = 60 - int(now - self.history[client_ip][0])
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMITED",
                            "message": f"Too many requests. Retry after {retry_after}s.",
                            "retryable": True,
                            "extra": {"retry_after": retry_after}
                        }
                    },
                    headers={"Retry-After": str(retry_after)}
                )

            self.history[client_ip].append(now)

        return await call_next(request)

    async def _cleanup_loop(self):
        """Periodically removes inactive IP records to prevent memory leak."""
        while True:
            await asyncio.sleep(300) # Every 5 minutes
            now = time.time()
            async with self._lock:
                to_delete = [ip for ip, hist in self.history.items() if not hist or now - hist[-1] > 3600]
                for ip in to_delete:
                    del self.history[ip]

async def error_handler_middleware(request: Request, call_next):
    """
    Catches all exceptions and converts them to structured JSON responses.
    Specifically maps Pydantic ValidationErrors and custom FFErrors.
    """
    try:
        return await call_next(request)
    except FFError as e:
        status_code = ERROR_HTTP_MAP.get(e.code, 500)
        return JSONResponse(
            status_code=status_code,
            content={
                "metadata": {
                    "request_uid": request.query_params.get("uid", "unknown"),
                    "request_region": request.query_params.get("region", "unknown"),
                    "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "response_time_ms": 0,
                    "api_version": settings.OB_VERSION,
                    "cache_hit": False
                },
                "data": None,
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "retryable": e.retryable,
                    "extra": e.extra
                }
            }
        )
    except ValidationError as e:
        # Map Pydantic validation errors to FFError INVALID_UID/REGION
        err_msg = e.errors()[0]["msg"]
        code = ErrorCode.INVALID_UID if "UID" in err_msg.upper() else ErrorCode.INVALID_REGION
        return JSONResponse(
            status_code=400,
            content={
                "metadata": {
                    "request_uid": request.query_params.get("uid", "unknown"),
                    "request_region": request.query_params.get("region", "unknown"),
                    "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "response_time_ms": 0,
                    "api_version": settings.OB_VERSION,
                    "cache_hit": False
                },
                "data": None,
                "error": {
                    "code": code,
                    "message": err_msg,
                    "retryable": False,
                    "extra": None
                }
            }
        )
    except Exception as e:
        logger.exception("Unhandled server error")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": f"An unexpected error occurred: {str(e)}",
                    "retryable": True,
                    "extra": None
                }
            }
        )
