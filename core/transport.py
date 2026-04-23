import asyncio
import aiohttp
import logging
import time
from typing import Optional, Dict, Any
from config.settings import settings
from core.auth import jwt_manager
from api.errors import FFError, ErrorCode

logger = logging.getLogger(__name__)

class AsyncTransport:
    """
    Handles asynchronous HTTP requests to Garena servers with:
    - Shared aiohttp.ClientSession
    - JWT Bearer Authentication
    - OB Version and Unity Headers
    - Exponential Backoff & Retry Policy
    - Rate Limit (429) & Auth (401) awareness
    """
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """Lazily initializes the aiohttp ClientSession."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "FreeFire/1.103.1 (Android 13; Pixel 7)",
                    "X-Unity-Version": "2022.3.12f1",
                    "Accept": "application/x-protobuf",
                    "Connection": "keep-alive"
                }
            )
        return self._session

    async def close(self):
        """Gracefully closes the shared session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def post(self, url: str, data: bytes, retry_count: int = 4) -> bytes:
        """
        Executes a POST request with exponential backoff and specialized error handling.
        """
        for attempt in range(1, retry_count + 1):
            try:
                headers = {
                    "Content-Type": "application/x-protobuf",
                    "X-Garena-OB": settings.OB_VERSION
                }

                # Attach JWT Token
                try:
                    token = await jwt_manager.get_token()
                    headers["Authorization"] = f"Bearer {token}"
                except Exception as e:
                    logger.error(f"Auth token retrieval failed: {e}")
                    if attempt == 1: raise # Fail fast on first attempt if auth is dead

                async with self.session.post(url, data=data, headers=headers, timeout=12) as resp:
                    # SUCCESS
                    if resp.status == 200:
                        return await resp.read()

                    # AUTH EXPIRED (401)
                    if resp.status == 401:
                        logger.warning("Received 401 Unauthorized. Forcing JWT refresh...")
                        jwt_manager.force_refresh()
                        if attempt < retry_count:
                            continue # Immediate retry after refresh
                        raise FFError(ErrorCode.AUTH_FAILED, "Authentication failed after multiple refreshes.")

                    # PLAYER NOT FOUND (404)
                    if resp.status == 404:
                        # FM-02: Suggest alternative regions
                        raise FFError(
                            ErrorCode.PLAYER_NOT_FOUND,
                            "Player UID not found in this region. Player may exist in: SG, IND, BR, or ID.",
                            retryable=False
                        )

                    # RATE LIMITED (429)
                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 10))
                        logger.warning(f"Garena Rate Limit (429). Waiting {retry_after}s...")
                        if attempt < retry_count:
                            await asyncio.sleep(retry_after)
                            continue
                        raise FFError(
                            ErrorCode.RATE_LIMITED,
                            "Exceeded Garena API rate limits.",
                            extra={"retry_after": retry_after}
                        )

                    # SERVER ERRORS (5xx)
                    if resp.status >= 500:
                        logger.error(f"Garena Server Error ({resp.status}). Attempt {attempt}/{retry_count}")
                        if attempt < retry_count:
                            await self._backoff(attempt)
                            continue
                        raise FFError(ErrorCode.SERVICE_UNAVAILABLE, "Garena services are currently unavailable (5xx).")

                    # UNEXPECTED CODES
                    body = await resp.text()
                    logger.error(f"Unexpected Garena Response {resp.status}: {body}")
                    raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Unexpected Garena response: {resp.status}")

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Network error on attempt {attempt}: {e}")
                if attempt < retry_count:
                    await self._backoff(attempt)
                    continue
                raise FFError(ErrorCode.TIMEOUT, "Connection to Garena timed out.")

    async def _backoff(self, attempt: int):
        """Exponential backoff: 1s, 3s, 7s..."""
        wait = (2 ** attempt) - 1
        await asyncio.sleep(wait)

# Singleton instance
transport = AsyncTransport()
