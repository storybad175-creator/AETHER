import time
import asyncio
import logging
from typing import Any, Dict, Optional, Tuple
from config.settings import settings

logger = logging.getLogger(__name__)

class TTLCache:
    """Thread-safe TTL Cache with LRU eviction."""

    def __init__(self):
        self._store: Dict[Tuple[str, str], Tuple[Any, float]] = {}
        self._lock = asyncio.Lock()
        self._max_entries = settings.CACHE_MAX_ENTRIES
        self._ttl = settings.CACHE_TTL_SECONDS

    async def get(self, uid: str, region: str) -> Optional[Any]:
        """Returns cached data if not expired, else None."""
        key = (uid, region)
        async with self._lock:
            if key not in self._store:
                return None

            data, expires_at = self._store[key]
            if time.time() > expires_at:
                del self._store[key]
                return None

            return data

    async def set(self, uid: str, region: str, data: Any):
        """Stores data in cache with TTL and handles eviction."""
        key = (uid, region)
        expires_at = time.time() + self._ttl

        async with self._lock:
            # Eviction policy: Remove 50 oldest if full
            if len(self._store) >= self._max_entries:
                logger.debug("Cache full, evicting 50 oldest entries.")
                # Sort by expiry time (proxy for insertion time)
                sorted_keys = sorted(self._store.keys(), key=lambda k: self._store[k][1])
                for k in sorted_keys[:50]:
                    del self._store[k]

            self._store[key] = (data, expires_at)

    def clear(self):
        """Clears all cached entries."""
        self._store.clear()

cache = TTLCache()
