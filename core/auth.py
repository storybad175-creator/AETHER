import asyncio
import time
import aiohttp
from typing import Optional
from config.settings import settings

class JWTManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JWTManager, cls).__new__(cls)
            cls._instance._token = None
            cls._instance._expires_at = 0
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    async def get_token(self, session: aiohttp.ClientSession) -> str:
        async with self._lock:
            if self._token and time.time() < self._expires_at - 60:
                return self._token

            await self._refresh(session)
            return self._token

    async def _refresh(self, session: aiohttp.ClientSession):
        url = "https://loginbp.ggblueshark.com/MajorLogin"
        payload = {
            "uid": settings.GARENA_GUEST_UID,
            "token": settings.GARENA_GUEST_TOKEN,
            "region": "IND" # Base region for auth
        }

        async with session.post(url, json=payload, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                self._token = data.get("jwt")
                # Assume 1 hour expiry if not provided
                self._expires_at = time.time() + data.get("expires_in", 3600)
            else:
                raise Exception(f"Auth failed with status {resp.status}")

    def force_refresh(self):
        self._expires_at = 0

jwt_manager = JWTManager()
