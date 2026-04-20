import time
import asyncio
import logging
from typing import Optional, Any, Dict, Tuple
from config.settings import settings

logger = logging.getLogger(__name__)

class TTLCache:
    """
    In-memory TTL cache with LRU-ish eviction and concurrency locks.
    Prevents cache stampedes by using a lock per key.
    """
    def __init__(self):
        self._store: Dict[Tuple[str, str], Tuple[Any, float]] = {}
        self._locks: Dict[Tuple[str, str], asyncio.Lock] = {}
        self._master_lock = asyncio.Lock()

    def _get_key(self, uid: str, region: str) -> Tuple[str, str]:
        return (str(uid), region.upper())

    async def get_lock(self, uid: str, region: str) -> asyncio.Lock:
        key = self._get_key(uid, region)
        async with self._master_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]

    def get(self, uid: str, region: str) -> Optional[Any]:
        key = self._get_key(uid, region)
        if key in self._store:
            data, expires_at = self._store[key]
            if time.time() < expires_at:
                return data
            else:
                # Expired
                del self._store[key]
        return None

    def set(self, uid: str, region: str, data: Any):
        key = self._get_key(uid, region)

        # Eviction policy
        if len(self._store) >= settings.CACHE_MAX_ENTRIES:
            self._evict()

        expires_at = time.time() + settings.CACHE_TTL_SECONDS
        self._store[key] = (data, expires_at)

    def _evict(self):
        """Evicts the 50 oldest entries based on expiry time."""
        logger.info("Cache limit reached. Evicting oldest entries...")
        # Sort by expires_at (the second element in the tuple)
        sorted_keys = sorted(self._store.keys(), key=lambda k: self._store[k][1])
        for i in range(min(50, len(sorted_keys))):
            del self._store[sorted_keys[i]]
            if sorted_keys[i] in self._locks:
                 # Clean up locks as well to prevent memory leak
                 del self._locks[sorted_keys[i]]

# Singleton instance
cache = TTLCache()
