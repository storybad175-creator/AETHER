import time
import asyncio
from typing import Dict, Any, Optional, Tuple
from config.settings import settings

class TTLCache:
    def __init__(self):
        # (uid, region) -> (data, expires_at)
        self._store: Dict[Tuple[str, str], Tuple[Any, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, uid: str, region: str) -> Optional[Any]:
        async with self._lock:
            key = (uid, region)
            if key in self._store:
                data, expires_at = self._store[key]
                if time.time() < expires_at:
                    return data
                else:
                    del self._store[key]
            return None

    async def set(self, uid: str, region: str, data: Any):
        async with self._lock:
            if len(self._store) >= settings.CACHE_MAX_ENTRIES:
                await self._evict_oldest()

            key = (uid, region)
            expires_at = time.time() + settings.CACHE_TTL_SECONDS
            self._store[key] = (data, expires_at)

    async def _evict_oldest(self):
        # Remove 50 oldest entries
        sorted_items = sorted(self._store.items(), key=lambda x: x[1][1])
        for key, _ in sorted_items[:50]:
            del self._store[key]

cache = TTLCache()
