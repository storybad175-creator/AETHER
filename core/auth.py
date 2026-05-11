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
    Includes auto-refresh and proactive expiry handling.
    """
    def __init__(self):
        self._token: Optional[str] = None
        self._expires_at: float = 0
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        """
        Returns a valid JWT token.
        Refreshes if the token is missing, expired, or near expiry.
        """
        async with self._lock:
            # Proactive refresh: if token expires in less than 60 seconds
            if not self._token or time.time() > (self._expires_at - 60):
                await self.refresh()
            return self._token

    async def refresh(self):
        """
        Performs the MajorLogin request to obtain a new JWT.
        """
        from core.transport import transport # Local import to avoid circular dependency

        logger.info("Refreshing Garena MajorLogin JWT...")

        url = "https://loginbp.ggblueshark.com/MajorLogin"
        payload = {
            "uid": settings.GARENA_GUEST_UID,
            "token": settings.GARENA_GUEST_TOKEN,
            "region": "SG" # MajorLogin usually uses a stable region
        }

        try:
            # We use a raw post here to avoid bearer token loop
            async with transport.session.post(url, json=payload, timeout=10) as resp:
                if resp.status != 200:
                    logger.error(f"MajorLogin failed with status {resp.status}")
                    raise FFError(
                        ErrorCode.AUTH_FAILED,
                        "Failed to authenticate with Garena MajorLogin endpoint."
                    )

                data = await resp.json()
                token = data.get("jwt")
                if not token:
                    raise FFError(ErrorCode.AUTH_FAILED, "No JWT found in MajorLogin response.")

                self._token = token

                # Default expiry 24 hours if not provided
                expires_in = data.get("expires_in", 86400)
                self._expires_at = time.time() + float(expires_in)

                logger.info(f"JWT refreshed successfully. Expires at: {time.ctime(self._expires_at)}")

        except Exception as e:
            if isinstance(e, FFError):
                raise
            logger.exception("Unexpected error during JWT refresh")
            raise FFError(ErrorCode.AUTH_FAILED, f"JWT refresh failed: {str(e)}")

    def force_refresh(self):
        """Invalidates current token to trigger refresh on next get_token call."""
        self._token = None
        self._expires_at = 0

# Singleton instance
jwt_manager = JWTManager()
