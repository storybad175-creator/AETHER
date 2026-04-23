import time
import asyncio
import logging
from typing import Optional
from config.settings import settings
from api.errors import FFError, ErrorCode

logger = logging.getLogger(__name__)

class JWTManager:
    """
    Manages the Garena MajorLogin JWT authentication lifecycle.
    Includes auto-refresh, thread-safe access, and proactive expiry handling.
    """
    def __init__(self):
        self._token: Optional[str] = None
        self._expires_at: float = 0
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        """
        Returns a valid JWT token.
        Refreshes if the token is missing, expired, or within 60 seconds of expiry.
        """
        async with self._lock:
            now = time.time()
            if not self._token or now > (self._expires_at - 60):
                await self.refresh()
            return self._token

    async def refresh(self):
        """
        Performs the Garena MajorLogin request to obtain a new JWT.
        Uses guest credentials from settings.
        """
        # Local import to avoid circular dependency with core.transport
        from core.transport import transport

        logger.info("Initiating Garena MajorLogin JWT refresh...")

        url = "https://loginbp.ggblueshark.com/MajorLogin"
        payload = {
            "uid": settings.GARENA_GUEST_UID,
            "token": settings.GARENA_GUEST_TOKEN,
            "region": "SG" # Stable region for auth endpoint
        }

        try:
            # Note: We use the session directly to avoid bearer token recursion in transport.post
            async with transport.session.post(url, json=payload, timeout=10) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error(f"MajorLogin failed ({resp.status}): {body}")
                    raise FFError(
                        ErrorCode.AUTH_FAILED,
                        f"Garena authentication failed with status {resp.status}.",
                        retryable=True
                    )

                data = await resp.json()
                token = data.get("jwt")
                if not token:
                    logger.error("MajorLogin response missing 'jwt' field.")
                    raise FFError(ErrorCode.AUTH_FAILED, "MajorLogin response missing JWT.")

                self._token = token
                # Default to 24 hours (86400s) if expires_in is missing
                expires_in = float(data.get("expires_in", 86400))
                self._expires_at = time.time() + expires_in

                logger.info(f"JWT refreshed successfully. Expires at: {time.ctime(self._expires_at)}")

        except asyncio.TimeoutError:
            logger.error("MajorLogin request timed out.")
            raise FFError(ErrorCode.TIMEOUT, "Authentication request timed out.", retryable=True)
        except Exception as e:
            if isinstance(e, FFError):
                raise
            logger.exception("Unexpected error during JWT refresh")
            raise FFError(ErrorCode.AUTH_FAILED, f"JWT refresh failed: {str(e)}", retryable=True)

    def force_refresh(self):
        """Invalidates current token to trigger a refresh on the next request."""
        self._token = None
        self._expires_at = 0

# Singleton instance
jwt_manager = JWTManager()
