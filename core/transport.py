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
    Handles asynchronous HTTP requests with exponential backoff,
    retries, and JWT authentication.
    """
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "FreeFire/1.103.1 (Android 13; Pixel 7)",
                    "X-Unity-Version": "2022.3.12f1",
                    "Accept": "application/x-protobuf"
                }
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def post(self, url: str, data: bytes, retry_count: int = 4) -> bytes:
        """
        Performs a POST request with retry logic and failure mode handling.
        """
        for attempt in range(1, retry_count + 1):
            try:
                headers = {
                    "Content-Type": "application/x-protobuf",
                    "X-Garena-OB": settings.OB_VERSION
                }

                try:
                    token = await jwt_manager.get_token()
                    if token:
                        headers["Authorization"] = f"Bearer {token}"
                except Exception as e:
                    logger.warning(f"Could not retrieve JWT token: {e}. Attempting without auth.")

                async with self.session.post(url, data=data, headers=headers, timeout=12) as resp:
                    if resp.status == 200:
                        return await resp.read()

                    if resp.status == 401:
                        logger.warning("Received 401 Unauthorized. Refreshing JWT and retrying...")
                        jwt_manager.force_refresh()
                        if attempt < retry_count:
                            continue
                        raise FFError(ErrorCode.AUTH_FAILED, "Authentication failed after refresh.")

                    if resp.status == 404:
                        raise FFError(
                            ErrorCode.PLAYER_NOT_FOUND,
                            "Player UID not found in this region. Player may exist in another region. Try: SG, IND, BR, ID."
                        )

                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 10))
                        logger.warning(f"Rate limited (429). Retrying after {retry_after}s...")
                        if attempt < retry_count:
                            await asyncio.sleep(retry_after)
                            continue
                        raise FFError(
                            ErrorCode.RATE_LIMITED,
                            "Exceeded Garena API rate limits.",
                            extra={"retry_after_seconds": retry_after}
                        )

                    if resp.status >= 500:
                        logger.error(f"Garena server error ({resp.status}). Attempt {attempt}/{retry_count}")
                        if attempt < retry_count:
                            await self._backoff(attempt)
                            continue
                        raise FFError(ErrorCode.SERVICE_UNAVAILABLE, "Garena services are currently unavailable.")

                    # Handle other non-200 codes
                    body = await resp.text()
                    logger.error(f"Unexpected response {resp.status}: {body}")
                    raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Unexpected Garena response: {resp.status}")

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Network error on attempt {attempt}: {e}")
                if attempt < retry_count:
                    await self._backoff(attempt)
                    continue
                raise FFError(ErrorCode.TIMEOUT, "Connection to Garena timed out.")

    async def _backoff(self, attempt: int):
        """Exponential backoff: 1, 3, 7 seconds."""
        wait = (2 ** attempt) - 1
        await asyncio.sleep(wait)

# Singleton instance
transport = AsyncTransport()
