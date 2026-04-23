import time
import asyncio
import logging
from typing import Optional, Any, Dict, Tuple
from config.settings import settings

logger = logging.getLogger(__name__)

class TTLCache:
    """
    In-memory TTL cache with LRU-style eviction and concurrency locks.
    Prevents cache stampedes by using a lock per unique (uid, region) key.
    """
    def __init__(self):
        # Store: (uid, region) -> (data, expires_at)
        self._store: Dict[Tuple[str, str], Tuple[Any, float]] = {}
        # Locks: (uid, region) -> asyncio.Lock
        self._locks: Dict[Tuple[str, str], asyncio.Lock] = {}
        # Global lock for modifying self._locks dictionary
        self._master_lock = asyncio.Lock()

    def _get_key(self, uid: str, region: str) -> Tuple[str, str]:
        """Normalizes the cache key."""
        return (str(uid), region.upper())

    async def get_lock(self, uid: str, region: str) -> asyncio.Lock:
        """Retrieves or creates an asyncio.Lock for a specific UID/Region."""
        key = self._get_key(uid, region)
        async with self._master_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]

    def get(self, uid: str, region: str) -> Optional[Any]:
        """
        Retrieves an item from the cache if it exists and hasn't expired.
        """
        key = self._get_key(uid, region)
        if key in self._store:
            data, expires_at = self._store[key]
            if time.time() < expires_at:
                logger.debug(f"Cache HIT for {key}")
                return data
            else:
                # Expired - remove from store
                logger.debug(f"Cache EXPIRED for {key}")
                del self._store[key]
        return None

    def set(self, uid: str, region: str, data: Any):
        """
        Adds or updates an item in the cache with the configured TTL.
        """
        key = self._get_key(uid, region)

        # FM-07: Eviction policy if cache is full
        if len(self._store) >= settings.CACHE_MAX_ENTRIES:
            self._evict()

        expires_at = time.time() + settings.CACHE_TTL_SECONDS
        self._store[key] = (data, expires_at)
        logger.debug(f"Cache SET for {key}. Total entries: {len(self._store)}")

    def _evict(self):
        """
        Evicts the oldest entries (by expiration time) when the limit is reached.
        """
        logger.info(f"Cache capacity ({settings.CACHE_MAX_ENTRIES}) reached. Evicting oldest 10%...")

        # Sort keys by expiration time (oldest first)
        sorted_keys = sorted(self._store.keys(), key=lambda k: self._store[k][1])

        # Evict top 10% or at least 1
        num_to_evict = max(1, len(sorted_keys) // 10)
        for i in range(num_to_evict):
            key_to_del = sorted_keys[i]
            del self._store[key_to_del]
            # Optionally clean up locks too if they are not active
            if key_to_del in self._locks and not self._locks[key_to_del].locked():
                del self._locks[key_to_del]

# Singleton instance
cache = TTLCache()
