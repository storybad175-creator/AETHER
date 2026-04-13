import asyncio
import time
from typing import Dict, Any, Optional, Tuple

class TTLCache:
    def __init__(self, ttl: int, max_entries: int):
        self.ttl = ttl
        self.max_entries = max_entries
        self._store: Dict[Tuple[str, str], Tuple[Dict[str, Any], float]] = {}
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
            data, expires_at = self._store[key]
            if time.time() < expires_at:
                return data
            else:
                del self._store[key]
        return None

    def set(self, uid: str, region: str, data: Dict[str, Any]):
        key = (uid, region)
        if len(self._store) >= self.max_entries:
            self._evict_oldest()

        expires_at = time.time() + self.ttl
        self._store[key] = (data, expires_at)

    def _evict_oldest(self):
        # Evict 10% or at least 50 entries
        num_to_evict = max(50, self.max_entries // 10)
        # Sort by expiry time (oldest first)
        sorted_keys = sorted(self._store.keys(), key=lambda k: self._store[k][1])
        for i in range(min(num_to_evict, len(sorted_keys))):
            del self._store[sorted_keys[i]]
            if sorted_keys[i] in self._locks:
                # We don't necessarily need to delete the lock, but let's keep it tidy
                # if no one is waiting on it. In asyncio, this is tricky.
                # For now, we leave the locks to avoid deleting a lock being used.
                pass

from ff_api.config.settings import settings
cache = TTLCache(ttl=settings.CACHE_TTL_SECONDS, max_entries=settings.CACHE_MAX_ENTRIES)
