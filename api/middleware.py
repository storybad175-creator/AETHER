import time
import uuid
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from config.settings import settings
from api.errors import FFError, ERROR_HTTP_MAP

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # client_ip -> [(timestamp, count)]
        self.requests: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()

        # Clean up old requests
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < 60]

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

async def error_handler_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except FFError as e:
        status_code = ERROR_HTTP_MAP.get(e.code, 500)
        return JSONResponse(
            status_code=status_code,
            content={
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
                    "code": "SERVICE_UNAVAILABLE",
                    "message": f"An unexpected error occurred: {str(e)}",
                    "retryable": True
                }
            }
        )
