import time
import asyncio
from typing import Optional
import aiohttp
from ff_api.config.settings import settings

class JWTManager:
    _instance: Optional["JWTManager"] = None

    def __init__(self):
        self._token: Optional[str] = None
        self._expires: float = 0
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def get_token(self) -> str:
        async with self._lock:
            # Proactive refresh 60 seconds before expiry
            if self._token is None or time.time() > self._expires - 60:
                await self.refresh()
            return self._token

    async def refresh(self):
        url = "https://loginbp.ggblueshark.com/MajorLogin"
        payload = {
            "uid": settings.GARENA_GUEST_UID,
            "token": settings.GARENA_GUEST_TOKEN
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._token = data.get("jwt")
                        # Assuming 'expires_in' is in seconds from response
                        expires_in = data.get("expires_in", 3600)
                        self._expires = time.time() + expires_in
                    else:
                        # In production, we should log this failure (without leaking credentials)
                        raise Exception(f"Failed to refresh JWT: {resp.status}")
            except Exception:
                # Fallback or re-raise typed error in fetcher
                raise

jwt_manager = JWTManager.get_instance()
