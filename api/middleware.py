import time
import uuid
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from api.errors import FFError, ERROR_HTTP_MAP, ErrorCode
from fastapi.responses import JSONResponse
from config.settings import settings

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(list)
        self.cleanup_task = None

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()

        # Clean old requests
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < 60]

        if len(self.requests[client_ip]) >= settings.RATE_LIMIT_RPM:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Too many requests. Please slow down.",
                        "retryable": True
                    }
                },
                headers={"Retry-After": "60"}
            )

        self.requests[client_ip].append(now)
        return await call_next(request)

async def error_handler_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except FFError as e:
        status_code = ERROR_HTTP_MAP.get(e.code, 500)
        return JSONResponse(
            status_code=status_code,
            content={
                "metadata": {
                    "request_uid": "N/A",
                    "request_region": "N/A",
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
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": str(e),
                    "retryable": False
                }
            }
        )
