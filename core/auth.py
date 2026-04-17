import time
import asyncio
import aiohttp
from typing import Optional
from config.settings import settings
from api.errors import FFError, ErrorCode

class JWTManager:
    _instance: Optional['JWTManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JWTManager, cls).__new__(cls)
            cls._instance._token = None
            cls._instance._expires_at = 0
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    async def get_token(self) -> str:
        async with self._lock:
            # Proactive refresh: if token expires in less than 60 seconds
            if not self._token or time.time() > self._expires_at - 60:
                await self.refresh()
            return self._token

    async def refresh(self, session: Optional[aiohttp.ClientSession] = None):
        url = "https://loginbp.ggblueshark.com/MajorLogin"
        payload = {
            "uid": settings.GARENA_GUEST_UID,
            "token": settings.GARENA_GUEST_TOKEN,
            "login_type": 2  # Guest login
        }

        # Use shared transport session if available, otherwise create temporary one
        from core.transport import transport
        active_session = session or transport.session

        should_close = False
        if active_session is None or active_session.closed:
            active_session = aiohttp.ClientSession()
            should_close = True

        try:
            async with active_session.post(url, json=payload, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._token = data.get("jwt")
                    # Assuming token is valid for 24h if not specified, or parse from JWT
                    # For simplicity, we set a default 24h expiry if not provided
                    expires_in = data.get("expires_in", 86400)
                    self._expires_at = time.time() + expires_in
                else:
                    raise FFError(
                        ErrorCode.AUTH_FAILED,
                        "Failed to authenticate with Garena MajorLogin endpoint."
                    )
        except Exception as e:
            if isinstance(e, FFError):
                raise
            raise FFError(ErrorCode.AUTH_FAILED, f"JWT refresh failed: {str(e)}")
        finally:
            if should_close:
                await active_session.close()

jwt_manager = JWTManager()
