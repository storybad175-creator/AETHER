from enum import Enum
from typing import Optional, Dict, Any

class ErrorCode(str, Enum):
    INVALID_UID = "INVALID_UID"
    INVALID_REGION = "INVALID_REGION"
    PLAYER_NOT_FOUND = "PLAYER_NOT_FOUND"
    AUTH_FAILED = "AUTH_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DECODE_ERROR = "DECODE_ERROR"
    TIMEOUT = "TIMEOUT"

class FFError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        retryable: bool = False,
        extra: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.retryable = retryable
        self.extra = extra
        super().__init__(self.message)

# Mapping ErrorCode to HTTP Status Codes
ERROR_HTTP_MAP = {
    ErrorCode.INVALID_UID: 400,
    ErrorCode.INVALID_REGION: 400,
    ErrorCode.AUTH_FAILED: 401,
    ErrorCode.PLAYER_NOT_FOUND: 404,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
    ErrorCode.DECODE_ERROR: 503,
    ErrorCode.TIMEOUT: 503,
}
