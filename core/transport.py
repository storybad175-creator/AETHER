import asyncio
import aiohttp
import logging
from typing import Any, Dict, Optional
from config.settings import settings
from core.auth import jwt_manager
from api.errors import FFError, ErrorCode

logger = logging.getLogger(__name__)

class AsyncTransport:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def post(self, url: str, data: bytes) -> bytes:
        session = await self.get_session()

        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; Pixel 5 Build/RD1A.201105.003.C1)",
            "Content-Type": "application/x-protobuf",
            "X-Unity-Version": "2021.3.15f1",
            "ReleaseVersion": settings.OB_VERSION
        }

        retries = 0
        max_retries = 3
        backoff = [1, 3, 7]

        while retries <= max_retries:
            token = await jwt_manager.get_token(session)
            headers["Authorization"] = f"Bearer {token}"

            try:
                async with session.post(url, data=data, headers=headers, timeout=12) as resp:
                    if resp.status == 200:
                        return await resp.read()

                    if resp.status == 401:
                        jwt_manager.force_refresh()
                        if retries < max_retries:
                            retries += 1
                            continue
                        raise FFError(ErrorCode.AUTH_FAILED, "Garena authentication failed after refresh.")

                    if resp.status == 404:
                        raise FFError(ErrorCode.PLAYER_NOT_FOUND, "Player not found in this region.")

                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 10))
                        if retries < max_retries:
                            await asyncio.sleep(retry_after)
                            retries += 1
                            continue
                        raise FFError(ErrorCode.RATE_LIMITED, "Garena API rate limit exceeded.", retryable=True, extra={"retry_after": retry_after})

                    if resp.status >= 500:
                        if retries < max_retries:
                            await asyncio.sleep(backoff[retries])
                            retries += 1
                            continue
                        raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Garena service error: {resp.status}")

                    raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Unexpected HTTP status: {resp.status}")

            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                if retries < max_retries:
                    await asyncio.sleep(backoff[retries])
                    retries += 1
                    continue
                raise FFError(ErrorCode.TIMEOUT, f"Network timeout or error: {str(e)}", retryable=True)

        raise FFError(ErrorCode.SERVICE_UNAVAILABLE, "Max retries reached.")

transport = AsyncTransport()
