import time
import asyncio
import aiohttp
from typing import Optional
from config.settings import settings

class JWTManager:
    _instance: Optional['JWTManager'] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JWTManager, cls).__new__(cls)
            cls._instance._token = None
            cls._instance._expires_at = 0.0
        return cls._instance

    async def get_token(self, session: aiohttp.ClientSession) -> str:
        """Returns a valid JWT token, refreshing it if necessary."""
        async with self._lock:
            # Proactive refresh: if token is missing or expires in less than 60 seconds
            if not self._token or time.time() > self._expires_at - 60:
                await self._refresh(session)
            return self._token

    async def _refresh(self, session: aiohttp.ClientSession):
        """Fetches a new JWT token from Garena's MajorLogin endpoint."""
        url = "https://loginbp.ggblueshark.com/MajorLogin"
        payload = {
            "uid": settings.GARENA_GUEST_UID,
            "token": settings.GARENA_GUEST_TOKEN,
            "login_type": 1, # Guest login
        }

        try:
            async with session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    self._token = data.get("access_token")
                    # Assuming token is valid for 24 hours if not specified
                    expires_in = data.get("expires_in", 86400)
                    self._expires_at = time.time() + expires_in
                else:
                    # In a real scenario, handle specific error codes
                    raise Exception(f"Failed to refresh JWT: {response.status}")
        except Exception as e:
            # Silently fail or log, but ensure the system knows the token is invalid
            self._token = None
            self._expires_at = 0.0
            raise e

    def force_refresh(self):
        """Invalidates the current token to force a refresh on next get_token call."""
        self._token = None
        self._expires_at = 0.0

jwt_manager = JWTManager()
