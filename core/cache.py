import asyncio
import time
from typing import Dict, Any, Optional, Tuple
from config.settings import settings

class TTLCache:
    def __init__(self, ttl: int = settings.CACHE_TTL_SECONDS, max_size: int = settings.CACHE_MAX_ENTRIES):
        self._ttl = ttl
        self._max_size = max_size
        self._store: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self._expires: Dict[Tuple[str, str], float] = {}
        self._lock = asyncio.Lock()
        self._locks: Dict[Tuple[str, str], asyncio.Lock] = {}

    async def get_lock(self, key: Tuple[str, str]) -> asyncio.Lock:
        async with self._lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]

    async def get(self, uid: str, region: str) -> Optional[Dict[str, Any]]:
        key = (uid, region)
        async with await self.get_lock(key):
            if key in self._store:
                if time.time() < self._expires[key]:
                    return self._store[key]
                else:
                    # Expired
                    del self._store[key]
                    del self._expires[key]
            return None

    async def set(self, uid: str, region: str, value: Dict[str, Any]):
        key = (uid, region)
        async with await self.get_lock(key):
            if len(self._store) >= self._max_size:
                await self._evict()

            self._store[key] = value
            self._expires[key] = time.time() + self._ttl

    async def _evict(self):
        """Evicts the oldest 50 entries based on expiration time."""
        # Sort by expiration time (oldest first)
        sorted_keys = sorted(self._expires.keys(), key=lambda k: self._expires[k])
        for key in sorted_keys[:50]:
            self._store.pop(key, None)
            self._expires.pop(key, None)
            self._locks.pop(key, None)

cache = TTLCache()
