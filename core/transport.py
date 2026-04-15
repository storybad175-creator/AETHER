import asyncio
import aiohttp
import time
from typing import Any, Dict, Optional
from config.settings import settings
from core.auth import jwt_manager
from api.errors import FFError, ErrorCode

class AsyncTransport:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def post(self, url: str, data: bytes) -> bytes:
        session = await self.get_session()
        token = await jwt_manager.get_token(session)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-protobuf",
            "User-Agent": f"Garena/FreeFire/OB{settings.OB_VERSION} (Android)",
            "X-OB-Version": settings.OB_VERSION,
            "X-Unity-Version": "2022.3.12f1"
        }

        retries = [0, 1, 3, 7]
        for delay in retries:
            if delay > 0:
                await asyncio.sleep(delay)

            try:
                async with session.post(url, data=data, headers=headers, timeout=12) as resp:
                    if resp.status == 200:
                        return await resp.read()
                    elif resp.status == 401:
                        jwt_manager.force_refresh()
                        # Token will be refreshed on next attempt
                        continue
                    elif resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 10))
                        await asyncio.sleep(retry_after)
                        continue
                    elif resp.status == 404:
                        raise FFError(ErrorCode.PLAYER_NOT_FOUND, "Player not found in this region.")
                    elif resp.status >= 500:
                        continue
                    else:
                        raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Garena API returned status {resp.status}")
            except asyncio.TimeoutError:
                continue
            except aiohttp.ClientError as e:
                raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Network error: {str(e)}")

        raise FFError(ErrorCode.TIMEOUT, "Request timed out after multiple retries.")

transport = AsyncTransport()
