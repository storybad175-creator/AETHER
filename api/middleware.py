import time
import uuid
import logging
import asyncio
from typing import Dict, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from api.errors import FFError, ErrorCode, ERROR_HTTP_MAP
from config.settings import settings
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.visits: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task = None
        self._cleanup_lock = asyncio.Lock()

    async def _cleanup_loop(self):
        """Periodically removes inactive client IP records."""
        while True:
            await asyncio.sleep(300) # Every 5 minutes
            async with self._lock:
                now = time.time()
                to_delete = [ip for ip, ts in self.visits.items() if not ts or now - ts[-1] > 300]
                for ip in to_delete:
                    del self.visits[ip]

    async def dispatch(self, request: Request, call_next):
        # Thread-safe/Async-safe start of cleanup task
        if self._cleanup_task is None:
            async with self._cleanup_lock:
                if self._cleanup_task is None:
                    self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        client_ip = request.client.host
        now = time.time()

        async with self._lock:
            # Filter timestamps within the last 60 seconds
            self.visits[client_ip] = [t for t in self.visits.get(client_ip, []) if now - t < 60]

            if len(self.visits[client_ip]) >= settings.RATE_LIMIT_RPM:
                return JSONResponse(
                    status_code=429,
                    content={
                        "metadata": {
                            "request_uid": "N/A",
                            "request_region": "N/A",
                            "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                            "response_time_ms": 0,
                            "api_version": settings.OB_VERSION,
                            "cache_hit": False
                        },
                        "data": None,
                        "error": {
                            "code": "RATE_LIMITED",
                            "message": "Too many requests. Please try again later.",
                            "retryable": True,
                            "extra": {"retry_after_seconds": 60}
                        }
                    },
                    headers={"Retry-After": "60"}
                )

            self.visits[client_ip].append(now)

        return await call_next(request)

async def error_handler_middleware(request: Request, call_next):
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
                    "request_uid": "N/A",
                    "request_region": "N/A",
                    "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    "response_time_ms": 0,
                    "api_version": settings.OB_VERSION,
                    "cache_hit": False
                },
                "data": None,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": exc.errors()[0]["msg"],
                    "retryable": False
                }
            }
        )
    except Exception as exc:
        logger.exception("Unhandled internal exception")
        return JSONResponse(
            status_code=500,
            content={
                "metadata": {
                    "request_uid": "N/A",
                    "request_region": "N/A",
                    "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    "response_time_ms": 0,
                    "api_version": settings.OB_VERSION,
                    "cache_hit": False
                },
                "data": None,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected internal error occurred.",
                    "retryable": False
                }
            }
        )
