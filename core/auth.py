import time
import asyncio
import aiohttp
from typing import Optional
from config.settings import settings
from api.errors import FFError, ErrorCode

class JWTManager:
    """Manages the lifecycle of the Garena MajorLogin JWT."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JWTManager, cls).__new__(cls)
            cls._instance._token = None
            cls._instance._expires_at = 0
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    async def get_token(self) -> str:
        """Returns a valid JWT, refreshing it if necessary."""
        async with self._lock:
            # Refresh if token is missing or near expiry (within 60s)
            if not self._token or time.time() > (self._expires_at - 60):
                await self.refresh()
            return self._token

    async def refresh(self):
        """Fetches a new JWT from Garena's MajorLogin endpoint."""
        url = "https://loginbp.ggblueshark.com/MajorLogin"
        payload = {
            "guest_id": settings.GARENA_GUEST_UID,
            "guest_token": settings.GARENA_GUEST_TOKEN,
            "release_version": settings.OB_VERSION
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as resp:
                    if resp.status != 200:
                        raise FFError(
                            ErrorCode.AUTH_FAILED,
                            f"MajorLogin failed with status {resp.status}"
                        )

                    data = await resp.json()
                    self._token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    self._expires_at = time.time() + expires_in

                    if not self._token:
                        raise FFError(
                            ErrorCode.AUTH_FAILED,
                            "MajorLogin response missing access_token"
                        )
        except aiohttp.ClientError as e:
            raise FFError(
                ErrorCode.SERVICE_UNAVAILABLE,
                f"Authentication service unreachable: {str(e)}"
            )
        except Exception as e:
            if isinstance(e, FFError):
                raise e
            raise FFError(
                ErrorCode.AUTH_FAILED,
                f"Unexpected authentication error: {str(e)}"
            )

    def force_refresh(self):
        """Invalidates current token to force a refresh on next get_token() call."""
        self._expires_at = 0

jwt_manager = JWTManager()
