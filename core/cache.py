import asyncio
import time
from typing import Dict, Any, Optional, Tuple

class TTLCache:
    def __init__(self, ttl: int, max_entries: int):
        self.ttl = ttl
        self.max_entries = max_entries
        self._store: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, uid: str, region: str) -> Optional[Dict[str, Any]]:
        """Retrieves an item from cache if it hasn't expired."""
        key = (uid, region)
        async with self._lock:
            if key in self._store:
                data, expires_at = self._store[key]
                if time.time() < expires_at:
                    return data
                else:
                    del self._store[key]
            return None

    async def set(self, uid: str, region: str, data: Any):
        """Stores an item in cache and handles eviction if full."""
        key = (uid, region)
        expires_at = time.time() + self.ttl

        async with self._lock:
            if len(self._store) >= self.max_entries:
                # Evict 50 oldest entries
                sorted_keys = sorted(self._store.keys(), key=lambda k: self._store[k][1])
                for k in sorted_keys[:50]:
                    del self._store[k]

            self._store[key] = (data, expires_at)

    async def get_lock(self, uid: str, region: str) -> asyncio.Lock:
        # For simplicity in this implementation, we use a single lock for the store.
        # A per-key lock would be better for high concurrency.
        return self._lock

from config.settings import settings
cache = TTLCache(ttl=settings.cache_ttl_seconds, max_entries=settings.cache_max_entries)
