import asyncio
import logging
import aiohttp
from typing import Optional, Any, Dict
from config.settings import settings
from core.auth import jwt_manager
from api.errors import FFError, ErrorCode

logger = logging.getLogger(__name__)

class AsyncTransport:
    """
    Handles all HTTP communication with Garena endpoints.
    Implements retries with exponential backoff and respects rate limit headers.
    """
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """Returns the shared ClientSession, creating it if needed."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15),
                headers={
                    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; SM-S901B Build/TP1A.220624.014)",
                    "X-Unity-Version": "2022.3.12f1",
                    "Release-Version": settings.OB_VERSION,
                    "Connection": "keep-alive"
                }
            )
        return self._session

    async def close(self):
        """Gracefully closes the shared session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def post(self, url: str, data: bytes, retry_count: int = 0) -> bytes:
        """
        Performs an authenticated POST request with exponential backoff retries.
        """
        max_retries = 3
        backoff_schedule = [1, 3, 7] # Seconds to wait between retries

        token = await jwt_manager.get_token()
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with self.session.post(url, data=data, headers=headers) as resp:
                # Handle Success
                if resp.status == 200:
                    return await resp.read()

                # Handle 401 (Auth Expired)
                if resp.status == 401 and retry_count < 1:
                    logger.warning("Received 401, refreshing token and retrying...")
                    await jwt_manager.get_token(force_refresh=True)
                    return await self.post(url, data, retry_count + 1)

                # Handle 404 (Player Not Found)
                if resp.status == 404:
                    raise FFError(
                        ErrorCode.PLAYER_NOT_FOUND,
                        "Player not found. The player may exist in another region. Try: SG, IND, BR, ID."
                    )

                # Handle 429 (Rate Limited)
                if resp.status == 429:
                    retry_after = int(resp.headers.get("Retry-After", 10))
                    if retry_count < max_retries:
                        logger.warning(f"Rate limited (429). Waiting {retry_after}s before retry {retry_count + 1}")
                        await asyncio.sleep(retry_after)
                        return await self.post(url, data, retry_count + 1)
                    else:
                        raise FFError(
                            ErrorCode.RATE_LIMITED,
                            f"Rate limit exceeded. Try again in {retry_after}s.",
                            extra={"retry_after": retry_after}
                        )

                # Handle 5xx or other transient errors
                if resp.status >= 500 and retry_count < max_retries:
                    wait_time = backoff_schedule[retry_count]
                    logger.warning(f"Server error {resp.status}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    return await self.post(url, data, retry_count + 1)

                # Final catch for all other non-200 responses
                raise FFError(
                    ErrorCode.SERVICE_UNAVAILABLE,
                    f"Garena API returned status {resp.status}."
                )

        except asyncio.TimeoutError:
            if retry_count < max_retries:
                wait_time = backoff_schedule[retry_count]
                logger.warning(f"Timeout occurred. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                return await self.post(url, data, retry_count + 1)
            raise FFError(ErrorCode.TIMEOUT, "Request timed out after multiple attempts.")

        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Network error: {str(e)}")

# Singleton instance
transport = AsyncTransport()
