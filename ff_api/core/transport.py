import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any
from ff_api.core.auth import jwt_manager
from ff_api.api.errors import FFError, ErrorCode

logger = logging.getLogger(__name__)

class AsyncTransport:
    _instance: Optional["AsyncTransport"] = None

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def post(self, url: str, data: bytes, ob_version: str) -> bytes:
        session = await self.get_session()
        token = await jwt_manager.get_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-protobuf",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-G991B Build/RP1A.200720.012)",
            "X-Unity-Version": "2021.3.15f1",
            "X-Garena-OB": ob_version,
        }

        retries = [0, 1, 3, 7]
        for i, delay in enumerate(retries):
            if delay > 0:
                await asyncio.sleep(delay)

            try:
                async with session.post(url, data=data, headers=headers, timeout=12) as resp:
                    if resp.status == 200:
                        return await resp.read()

                    if resp.status == 401:
                        logger.warning("JWT expired mid-session, refreshing...")
                        await jwt_manager.refresh()
                        # Update headers with new token for the retry
                        new_token = await jwt_manager.get_token()
                        headers["Authorization"] = f"Bearer {new_token}"
                        if i == len(retries) - 1:
                            raise FFError(ErrorCode.AUTH_FAILED, "Authentication failed after refresh.")
                        continue # Immediate retry on 401 if not last attempt

                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 10))
                        if i < len(retries) - 1:
                            await asyncio.sleep(retry_after)
                            continue
                        raise FFError(ErrorCode.RATE_LIMITED, "Rate limited by Garena.", extra={"retry_after": retry_after})

                    if resp.status == 404:
                        raise FFError(ErrorCode.PLAYER_NOT_FOUND, "Player not found in this region.")

                    if resp.status >= 500:
                        if i == len(retries) - 1:
                            raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Garena server error: {resp.status}")
                        continue

                    # Other errors
                    raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Unexpected response from Garena: {resp.status}")

            except asyncio.TimeoutError:
                if i == len(retries) - 1:
                    raise FFError(ErrorCode.TIMEOUT, "Request to Garena timed out.")
                continue
            except aiohttp.ClientError as e:
                if i == len(retries) - 1:
                    raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Connection error: {str(e)}")
                continue

        raise FFError(ErrorCode.SERVICE_UNAVAILABLE, "Failed to fetch data after retries.")

transport = AsyncTransport.get_instance()
