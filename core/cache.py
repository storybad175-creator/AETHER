import time
import logging
from typing import Optional, Dict, Any, Tuple
from config.settings import settings

logger = logging.getLogger(__name__)

class TTLCache:
    """
    In-memory TTL cache with LRU-style eviction.
    Thread-safe for use with asyncio.
    """
    def __init__(self, ttl: int, max_entries: int):
        self.ttl = ttl
        self.max_entries = max_entries
        self._store: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def get(self, uid: str, region: str) -> Optional[Any]:
        """
        Retrieves an item from the cache if it exists and has not expired.
        """
        key = (uid, region.upper())
        if key in self._store:
            entry = self._store[key]
            if time.time() < entry["expires_at"]:
                logger.debug(f"Cache hit: {uid} ({region})")
                return entry["data"]
            else:
                # Expired
                logger.debug(f"Cache expired: {uid} ({region})")
                del self._store[key]
        return None

    def set(self, uid: str, region: str, data: Any):
        """
        Stores an item in the cache, applying TTL and eviction logic.
        """
        key = (uid, region.upper())

        # Eviction logic: If full, remove 50 oldest entries (by expiration time)
        if len(self._store) >= self.max_entries:
            logger.info(f"Cache limit reached ({self.max_entries}). Evicting oldest entries.")
            # Sort by expiration time and take the first 50
            sorted_keys = sorted(self._store.keys(), key=lambda k: self._store[k]["expires_at"])
            for k in sorted_keys[:50]:
                del self._store[k]

        self._store[key] = {
            "data": data,
            "expires_at": time.time() + self.ttl
        }
        logger.debug(f"Cached: {uid} ({region})")

# Singleton instance using settings
cache = TTLCache(
    ttl=settings.CACHE_TTL_SECONDS,
    max_entries=settings.CACHE_MAX_ENTRIES
)
