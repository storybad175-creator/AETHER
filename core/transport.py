import asyncio
import aiohttp
import logging
from typing import Any, Dict, Optional
from config.settings import settings
from core.auth import jwt_manager
from api.errors import FFError, ErrorCode

logger = logging.getLogger(__name__)

class AsyncTransport:
    """Handles HTTP communication with Garena servers with retry logic."""

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def post(self, url: str, data: bytes, headers: Optional[Dict[str, str]] = None) -> bytes:
        """Performs an async POST request with exponential backoff retries."""
        session = await self._get_session()

        default_headers = {
            "User-Agent": "FreeFire/2026.04.11 (Android; OB53; Unity 2022.3.12f1)",
            "X-Unity-Version": "2022.3.12f1",
            "X-GA-OB": settings.OB_VERSION,
            "Content-Type": "application/x-protobuf",
            "Accept": "*/*",
            "Connection": "keep-alive"
        }

        if headers:
            default_headers.update(headers)

        retries = 0
        max_retries = 4
        backoff = [0, 1, 3, 7]

        while retries < max_retries:
            try:
                # Get fresh token for every retry to be safe
                token = await jwt_manager.get_token()
                default_headers["Authorization"] = f"Bearer {token}"

                if retries > 0:
                    await asyncio.sleep(backoff[retries])

                async with session.post(url, data=data, headers=default_headers, timeout=12) as resp:
                    if resp.status == 200:
                        return await resp.read()

                    if resp.status == 401:
                        logger.warning("Auth token expired, refreshing...")
                        jwt_manager.force_refresh()
                        if retries == 0:  # Immediate retry once on 401
                            retries += 1
                            continue
                        raise FFError(ErrorCode.AUTH_FAILED, "Authentication failed after refresh")

                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 10))
                        logger.warning(f"Rate limited. Waiting {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        retries += 1
                        continue

                    if resp.status == 404:
                        raise FFError(ErrorCode.PLAYER_NOT_FOUND, "Player not found in this region")

                    if 500 <= resp.status < 600:
                        logger.error(f"Server error {resp.status}, retrying...")
                        retries += 1
                        continue

                    # Other errors
                    error_body = await resp.text()
                    raise FFError(
                        ErrorCode.SERVICE_UNAVAILABLE,
                        f"Garena API returned status {resp.status}: {error_body}"
                    )

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.error(f"Network error on attempt {retries + 1}: {str(e)}")
                retries += 1
                if retries >= max_retries:
                    raise FFError(ErrorCode.TIMEOUT, f"Request timed out after {max_retries} attempts")
            except FFError:
                raise
            except Exception as e:
                logger.error(f"Unexpected error in transport: {str(e)}")
                raise FFError(ErrorCode.SERVICE_UNAVAILABLE, f"Transport error: {str(e)}")

        raise FFError(ErrorCode.SERVICE_UNAVAILABLE, "Max retries reached")

transport = AsyncTransport()
