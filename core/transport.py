import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any
from config.settings import settings
from core.auth import jwt_manager
from api.errors import FFError, ErrorCode

logger = logging.getLogger(__name__)

class AsyncTransport:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()

    async def get_session(self) -> aiohttp.ClientSession:
        async with self._lock:
            if self.session is None or self.session.closed:
                self.session = aiohttp.ClientSession(
                    headers={
                        "User-Agent": f"FreeFire/2026.4 (Android; {settings.ob_version})",
                        "X-Unity-Version": "2022.3.12f1",
                        "Release-Version": settings.ob_version,
                        "Content-Type": "application/x-protobuf"
                    }
                )
            return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def post(self, url: str, data: bytes, retries: int = 3) -> bytes:
        session = await self.get_session()

        for attempt in range(retries + 1):
            try:
                token = await jwt_manager.get_token(self)
                headers = {"Authorization": f"Bearer {token}"}

                async with session.post(url, data=data, headers=headers, timeout=12) as resp:
                    if resp.status == 200:
                        return await resp.read()

                    if resp.status == 401:
                        logger.warning("JWT expired. Refreshing...")
                        await jwt_manager.refresh(self)
                        if attempt < retries: continue
                        raise FFError(ErrorCode.AUTH_FAILED, "Authentication failed after refresh")

                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 10))
                        logger.warning(f"Rate limited. Waiting {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        if attempt < retries: continue
                        raise FFError(ErrorCode.RATE_LIMITED, "Exceeded rate limit", retryable=True)

                    if resp.status == 404:
                        raise FFError(ErrorCode.PLAYER_NOT_FOUND, "Player not found in this region")

                    if resp.status >= 500:
                        if attempt < retries:
                            wait = 2 ** attempt
                            await asyncio.sleep(wait)
                            continue
                        raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Garena server error: {resp.status}")

                    raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Unexpected HTTP error: {resp.status}")

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < retries:
                    wait = 2 ** attempt
                    await asyncio.sleep(wait)
                    continue
                raise FFError(ErrorCode.TIMEOUT, f"Network timeout: {str(e)}", retryable=True)

transport = AsyncTransport()
