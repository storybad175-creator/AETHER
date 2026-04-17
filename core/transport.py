import asyncio
import aiohttp
import time
from typing import Optional, Dict, Any
from config.settings import settings
from core.auth import jwt_manager
from api.errors import FFError, ErrorCode

class AsyncTransport:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "FreeFire/2022.3.12f1 (Android) OB53",
                    "X-Unity-Version": "2022.3.12f1",
                    "Release-Version": settings.OB_VERSION,
                    "Content-Type": "application/x-protobuf"
                }
            )

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def post(self, url: str, data: bytes, retries: int = 4) -> bytes:
        await self.ensure_session()

        for attempt in range(retries):
            token = await jwt_manager.get_token()
            headers = {"Authorization": f"Bearer {token}"}

            try:
                async with self.session.post(url, data=data, headers=headers, timeout=12) as resp:
                    if resp.status == 200:
                        return await resp.read()

                    if resp.status == 401:
                        await jwt_manager.refresh()
                        continue # Retry once automatically

                    if resp.status == 404:
                        raise FFError(ErrorCode.PLAYER_NOT_FOUND, "Player not found in this region.")

                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 10))
                        if attempt < retries - 1:
                            await asyncio.sleep(retry_after)
                            continue
                        raise FFError(ErrorCode.RATE_LIMITED, "Rate limit exceeded.", extra={"retry_after": retry_after})

                    if resp.status >= 500:
                        if attempt < retries - 1:
                            wait_time = [0, 1, 3, 7][attempt]
                            await asyncio.sleep(wait_time)
                            continue
                        raise FFError(ErrorCode.SERVICE_UNAVAILABLE, "Garena servers are currently unavailable.")

                    raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Unexpected HTTP {resp.status}")

            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                if attempt < retries - 1:
                    wait_time = [0, 1, 3, 7][attempt]
                    await asyncio.sleep(wait_time)
                    continue
                raise FFError(ErrorCode.TIMEOUT, f"Request timed out after {retries} attempts.")

        raise FFError(ErrorCode.SERVICE_UNAVAILABLE, "Maximum retries reached.")

transport = AsyncTransport()
