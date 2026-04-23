import time
import uuid
import logging
import asyncio
from typing import Dict, List, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from api.errors import FFError, ErrorCode, ERROR_HTTP_MAP
from config.settings import settings
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Injects a unique X-Request-ID into every response header."""
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Implements a simple in-memory sliding window rate limiter per client IP.
    Default: 30 requests per minute.
    """
    def __init__(self, app):
        super().__init__(app)
        self.visits: Dict[str, List[float]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    async def _cleanup_loop(self):
        """Periodically removes inactive client IP records to prevent memory leaks."""
        while True:
            await asyncio.sleep(300)
            now = time.time()
            to_delete = [ip for ip, ts in self.visits.items() if not ts or now - ts[-1] > 300]
            for ip in to_delete:
                del self.visits[ip]

    async def dispatch(self, request: Request, call_next):
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        client_ip = request.client.host
        now = time.time()

        # Sliding window: filter for timestamps within the last 60s
        self.visits[client_ip] = [t for t in self.visits.get(client_ip, []) if now - t < 60]

        if len(self.visits[client_ip]) >= settings.RATE_LIMIT_RPM:
            return JSONResponse(
                status_code=429,
                content={
                    "metadata": {
                        "request_uid": request.query_params.get("uid", "N/A"),
                        "request_region": request.query_params.get("region", "N/A"),
                        "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                        "response_time_ms": 0,
                        "api_version": settings.OB_VERSION,
                        "cache_hit": False
                    },
                    "data": None,
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Too many requests. Please respect the 30 RPM limit.",
                        "retryable": True,
                        "extra": {"retry_after": 60}
                    }
                },
                headers={"Retry-After": "60"}
            )

        self.visits[client_ip].append(now)
        return await call_next(request)

async def error_handler_middleware(request: Request, call_next):
    """
    Outermost middleware to catch all exceptions and return structured JSON.
    Converts FFErrors and Pydantic ValidationErrors into consistent PlayerResponse shapes.
    """
    try:
        return await call_next(request)
    except FFError as exc:
        status_code = ERROR_HTTP_MAP.get(exc.code, 500)
        return JSONResponse(
            status_code=status_code,
            content={
                "metadata": {
                    "request_uid": request.query_params.get("uid", "N/A"),
                    "request_region": request.query_params.get("region", "N/A"),
                    "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    "response_time_ms": 0,
                    "api_version": settings.OB_VERSION,
                    "cache_hit": False
                },
                "data": None,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "retryable": exc.retryable,
                    "extra": exc.extra
                }
            }
        )
    except ValidationError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "metadata": {
                    "request_uid": request.query_params.get("uid", "N/A"),
                    "request_region": request.query_params.get("region", "N/A"),
                    "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    "response_time_ms": 0,
                    "api_version": settings.OB_VERSION,
                    "cache_hit": False
                },
                "data": None,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": exc.errors()[0]["msg"],
                    "retryable": False,
                    "extra": {"detail": exc.errors()}
                }
            }
        )
    except Exception as exc:
        logger.exception("FATAL: Unhandled exception in middleware chain")
        return JSONResponse(
            status_code=500,
            content={
                "metadata": {
                    "request_uid": request.query_params.get("uid", "N/A"),
                    "request_region": request.query_params.get("region", "N/A"),
                    "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    "response_time_ms": 0,
                    "api_version": settings.OB_VERSION,
                    "cache_hit": False
                },
                "data": None,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"An unexpected internal error occurred: {type(exc).__name__}",
                    "retryable": False
                }
            }
        )
