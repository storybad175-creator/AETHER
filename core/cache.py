import asyncio
import time
from typing import Any, Dict, Optional, Tuple
from config.settings import settings

class TTLCache:
    def __init__(self):
        self._store: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self._locks: Dict[Tuple[str, str], asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def get_lock(self, uid: str, region: str) -> asyncio.Lock:
        key = (uid, region)
        async with self._global_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]

    def get(self, uid: str, region: str) -> Optional[Dict[str, Any]]:
        key = (uid, region)
        if key in self._store:
            item = self._store[key]
            if time.time() < item["expires_at"]:
                return item["data"]
            else:
                del self._store[key]
        return None

    def set(self, uid: str, region: str, data: Any):
        key = (uid, region)
        expires_at = time.time() + settings.CACHE_TTL_SECONDS

        # Eviction policy
        if len(self._store) >= settings.CACHE_MAX_ENTRIES:
            # Sort by expires_at and remove oldest 50
            sorted_keys = sorted(self._store.keys(), key=lambda k: self._store[k]["expires_at"])
            for k in sorted_keys[:50]:
                del self._store[k]
                if k in self._locks:
                    del self._locks[k]

        self._store[key] = {
            "data": data,
            "expires_at": expires_at
        }

cache = TTLCache()
