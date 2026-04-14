import time
import uuid
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from api.errors import FFError, ERROR_HTTP_MAP, ErrorCode
from api.schemas import PlayerResponse, ResponseMetadata, ErrorDetail
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
        self.requests = {}
        self.last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next):
        now = time.time()

        # Periodic cleanup of old IPs to prevent memory leaks
        if now - self.last_cleanup > 300:
            expired_threshold = now - 60
            ips_to_remove = [ip for ip, ts in self.requests.items() if not any(t > expired_threshold for t in ts)]
            for ip in ips_to_remove:
                del self.requests[ip]
            self.last_cleanup = now

        client_ip = request.client.host
        now = time.time()

        # Simple sliding window
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Clean old requests
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > now - 60]

        if len(self.requests[client_ip]) >= settings.RATE_LIMIT_RPM:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Too many requests. Please try again later.",
                        "retryable": True
                    }
                },
                headers={"Retry-After": "60"}
            )

        self.requests[client_ip].append(now)
        return await call_next(request)

async def error_handler(request: Request, exc: Exception):
    start_time = time.monotonic()
    if isinstance(exc, FFError):
        status_code = ERROR_HTTP_MAP.get(exc.code, 500)
        return JSONResponse(
            status_code=status_code,
            content=PlayerResponse(
                metadata=ResponseMetadata(
                    request_uid="N/A",
                    request_region="N/A",
                    fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    response_time_ms=0,
                    api_version="OB53",
                    cache_hit=False
                ),
                data=None,
                error=ErrorDetail(
                    code=exc.code,
                    message=exc.message,
                    retryable=exc.retryable,
                    extra=exc.extra
                )
            ).model_dump()
        )

    # Unexpected errors
    return JSONResponse(
        status_code=500,
        content=PlayerResponse(
            metadata=ResponseMetadata(
                request_uid="N/A",
                request_region="N/A",
                fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                response_time_ms=0,
                api_version="OB53",
                cache_hit=False
            ),
            data=None,
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message=str(exc),
                retryable=False
            )
        ).model_dump()
    )
