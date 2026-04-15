import asyncio
import time
from typing import Dict, Any, Optional
from config.settings import settings

class TTLCache:
    def __init__(self):
        self._store: Dict[tuple, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, uid: str, region: str) -> Optional[Dict[str, Any]]:
        key = (uid, region)
        async with self._lock:
            if key in self._store:
                entry = self._store[key]
                if time.time() < entry["expires_at"]:
                    return entry["data"]
                else:
                    del self._store[key]
            return None

    async def set(self, uid: str, region: str, data: Dict[str, Any]):
        key = (uid, region)
        async with self._lock:
            # Eviction policy
            if len(self._store) >= settings.CACHE_MAX_ENTRIES:
                # Remove oldest 50 entries
                sorted_keys = sorted(self._store.keys(), key=lambda k: self._store[k]["expires_at"])
                for i in range(min(50, len(sorted_keys))):
                    del self._store[sorted_keys[i]]

            self._store[key] = {
                "data": data,
                "expires_at": time.time() + settings.CACHE_TTL_SECONDS
            }

cache = TTLCache()
