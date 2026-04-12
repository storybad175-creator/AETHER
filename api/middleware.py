import uuid
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from api.errors import FFError, ErrorCode, ERROR_HTTP_MAP
from fastapi.responses import JSONResponse
from config.settings import settings
from collections import defaultdict

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rpm: int = settings.RATE_LIMIT_RPM):
        super().__init__(app)
        self.rpm = rpm
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()

        # Clean up old requests
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < 60]

        if len(self.requests[client_ip]) >= self.rpm:
            retry_after = 60 - (now - self.requests[client_ip][0])
            return JSONResponse(
                status_code=429,
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
                        "code": ErrorCode.RATE_LIMITED,
                        "message": f"Rate limit exceeded. Try again in {int(retry_after)} seconds.",
                        "retryable": True,
                        "extra": {"retry_after_seconds": int(retry_after)}
                    }
                },
                headers={"Retry-After": str(int(retry_after))}
            )

        self.requests[client_ip].append(now)
        return await call_next(request)

async def ff_error_handler(request: Request, exc: FFError):
    status_code = ERROR_HTTP_MAP.get(exc.code, 500)
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
                "code": exc.code,
                "message": exc.message,
                "retryable": exc.retryable,
                "extra": exc.extra
            }
        }
    )
