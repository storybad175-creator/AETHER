import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional
from core.auth import jwt_manager
from config.settings import settings

class AsyncTransport:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def post(self, url: str, data: bytes) -> bytes:
        """Sends an encrypted POST request with exponential backoff retry."""
        session = await self._get_session()

        max_attempts = 4
        for attempt in range(1, max_attempts + 1):
            try:
                token = await jwt_manager.get_token(session)
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/x-protobuf",
                    "User-Agent": "FreeFire/1.104.1 (Android; 13; en_US)",
                    "X-Unity-Version": "2021.3.15f1",
                    "X-GARENA-OB": settings.OB_VERSION,
                }

                async with session.post(url, data=data, headers=headers, timeout=12) as response:
                    if response.status == 200:
                        return await response.read()

                    if response.status == 401:
                        jwt_manager.force_refresh()
                        if attempt < max_attempts:
                            continue # Retry immediately once after refresh

                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 10))
                        await asyncio.sleep(retry_after)
                        continue

                    if response.status >= 500:
                        # Exponential backoff: 1, 3, 7 seconds
                        wait_time = (2 ** attempt) - 1
                        await asyncio.sleep(wait_time)
                        continue

                    # For 400, 404, etc., we don't retry here
                    response.raise_for_status()

            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                if attempt == max_attempts:
                    raise e
                wait_time = (2 ** attempt) - 1
                await asyncio.sleep(wait_time)

        raise Exception("Max retry attempts reached")

transport = AsyncTransport()
