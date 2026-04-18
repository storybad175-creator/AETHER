import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError
from api.errors import FFError, ErrorCode, ERROR_HTTP_MAP
from api.schemas import PlayerResponse, ResponseMetadata, ErrorDetail
from config.settings import settings
import json
import logging

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.visits = {} # IP -> list of timestamps
        self.last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()

        # Periodic cleanup of all IPs to prevent memory leak
        if now - self.last_cleanup > 300:
            self._cleanup_all(now)
            self.last_cleanup = now

        # Clean old visits for this IP
        if client_ip not in self.visits:
            self.visits[client_ip] = []

        self.visits[client_ip] = [t for t in self.visits[client_ip] if now - t < 60]

        if len(self.visits[client_ip]) >= settings.rate_limit_rpm:
            retry_after = 60 - (now - self.visits[client_ip][0])
            return Response(
                content=json.dumps({
                    "metadata": {
                        "request_uid": "N/A",
                        "request_region": "N/A",
                        "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                        "response_time_ms": 0,
                        "api_version": settings.ob_version,
                        "cache_hit": False
                    },
                    "data": None,
                    "error": {
                        "code": ErrorCode.RATE_LIMITED,
                        "message": "Too many requests. Please slow down.",
                        "retryable": True,
                        "extra": {"retry_after_seconds": int(retry_after)}
                    }
                }),
                status_code=429,
                media_type="application/json"
            )

        self.visits[client_ip].append(now)
        return await call_next(request)

    def _cleanup_all(self, now: float):
        """Removes inactive client IPs from the memory."""
        to_delete = []
        for ip, timestamps in self.visits.items():
            # If no activity in the last 60 seconds, mark for deletion
            if not timestamps or now - timestamps[-1] > 60:
                to_delete.append(ip)
        for ip in to_delete:
            del self.visits[ip]

async def error_handler_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except ValidationError as e:
        return Response(
            content=json.dumps({
                "metadata": {
                    "request_uid": "N/A",
                    "request_region": "N/A",
                    "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    "response_time_ms": 0,
                    "api_version": settings.ob_version,
                    "cache_hit": False
                },
                "data": None,
                "error": {
                    "code": ErrorCode.INVALID_UID if "uid" in str(e) else ErrorCode.INVALID_REGION,
                    "message": str(e),
                    "retryable": False,
                    "extra": None
                }
            }),
            status_code=400,
            media_type="application/json"
        )
    except FFError as e:
        status_code = ERROR_HTTP_MAP.get(e.code, 500)
        return Response(
            content=json.dumps({
                "metadata": {
                    "request_uid": "N/A",
                    "request_region": "N/A",
                    "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    "response_time_ms": 0,
                    "api_version": settings.ob_version,
                    "cache_hit": False
                },
                "data": None,
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "retryable": e.retryable,
                    "extra": e.extra
                }
            }),
            status_code=status_code,
            media_type="application/json"
        )
    except Exception as e:
        logger.exception("Unhandled exception")
        return Response(
            content=json.dumps({
                "metadata": {
                    "request_uid": "N/A",
                    "request_region": "N/A",
                    "fetched_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    "response_time_ms": 0,
                    "api_version": settings.ob_version,
                    "cache_hit": False
                },
                "data": None,
                "error": {
                    "code": ErrorCode.SERVICE_UNAVAILABLE,
                    "message": f"Internal server error: {str(e)}",
                    "retryable": False,
                    "extra": None
                }
            }),
            status_code=500,
            media_type="application/json"
        )
