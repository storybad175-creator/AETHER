import asyncio
import time
from typing import Optional
from config.settings import settings
from api.errors import FFError, ErrorCode

class JWTManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JWTManager, cls).__new__(cls)
            cls._instance._token = None
            cls._instance._expires_at = 0
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    async def get_token(self, transport=None) -> str:
        """Returns a valid JWT token, refreshing if necessary."""
        async with self._lock:
            if self._token and time.time() < self._expires_at - 60:
                return self._token

            if transport is None:
                # This should only happen if we haven't initialized transport yet
                # but need a token. In practice, transport is passed in.
                from core.transport import transport as global_transport
                transport = global_transport

            await self.refresh(transport)
            return self._token

    async def refresh(self, transport):
        """Fetches a new JWT from Garena MajorLogin endpoint."""
        url = "https://loginbp.ggblueshark.com/MajorLogin"
        payload = {
            "uid": settings.garena_guest_uid,
            "token": settings.garena_guest_token,
            "login_type": 2  # Guest login
        }

        # Avoid circular import by local import if needed,
        # but transport is passed in here.

        try:
            # Note: We use the raw aiohttp session from transport here
            # but without the auth header to avoid infinite recursion.
            async with transport.session.post(url, json=payload, timeout=10) as resp:
                if resp.status != 200:
                    raise FFError(
                        ErrorCode.AUTH_FAILED,
                        f"Garena login failed with status {resp.status}"
                    )

                data = await resp.json()
                self._token = data.get("jwt")
                # Tokens usually last 24h, we use the provided expiry or 23h default
                expires_in = data.get("expires_in", 82800)
                self._expires_at = time.time() + expires_in

                if not self._token:
                    raise FFError(ErrorCode.AUTH_FAILED, "No JWT returned from Garena")

        except Exception as e:
            if isinstance(e, FFError):
                raise
            raise FFError(ErrorCode.AUTH_FAILED, f"Authentication request failed: {str(e)}")

jwt_manager = JWTManager()
