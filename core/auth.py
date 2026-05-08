import time
import logging
import asyncio
from typing import Optional
from config.settings import settings
from api.errors import FFError, ErrorCode

logger = logging.getLogger(__name__)

class JWTManager:
    """
    Manages the Garena MajorLogin JWT lifecycle.
    Handles silent refreshes and proactive token updates.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JWTManager, cls).__new__(cls)
            cls._instance._token = None
            cls._instance._expires_at = 0.0
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    @property
    def is_expired(self) -> bool:
        """Checks if the current token is expired or close to expiry (within 60s)."""
        return time.time() > (self._expires_at - 60)

    async def get_token(self, force_refresh: bool = False) -> str:
        """Returns a valid JWT token, refreshing if necessary."""
        async with self._lock:
            if self._token is None or self.is_expired or force_refresh:
                await self.refresh()
            return self._token

    async def refresh(self):
        """
        Performs the Garena MajorLogin request to obtain a new JWT.
        Uses the shared aiohttp session from the transport module.
        """
        logger.info("Refreshing Garena JWT token...")

        # Local import to avoid circular dependency
        from core.transport import transport

        url = "https://loginbp.ggblueshark.com/MajorLogin"
        payload = {
            "uid": settings.GARENA_GUEST_UID,
            "token": settings.GARENA_GUEST_TOKEN,
            "region": "IND" # Region doesn't matter for MajorLogin
        }

        try:
            # We don't use transport.post here to avoid recursion and auth headers
            async with transport.session.post(url, json=payload, timeout=10) as resp:
                if resp.status != 200:
                    logger.error(f"MajorLogin failed with status {resp.status}")
                    raise FFError(ErrorCode.AUTH_FAILED, "Garena MajorLogin failed. Check guest credentials.")

                data = await resp.json()
                self._token = data.get("token")

                # Default to 24h if expiry not provided (unlikely)
                expires_in = data.get("expires_in", 86400)
                self._expires_at = time.time() + float(expires_in)

                if not self._token:
                    raise FFError(ErrorCode.AUTH_FAILED, "No token found in MajorLogin response.")

                logger.info("JWT token refreshed successfully.")

        except FFError:
            raise
        except Exception as e:
            logger.exception("Unexpected error during JWT refresh")
            raise FFError(ErrorCode.AUTH_FAILED, f"JWT refresh failed: {str(e)}")

# Singleton instance
jwt_manager = JWTManager()
