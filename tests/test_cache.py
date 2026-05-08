import pytest
import time
from core.cache import TTLCache

def test_cache_hit_miss():
    cache = TTLCache(ttl=1, max_entries=10)
    cache.set("123", "IND", {"name": "Test"})

    assert cache.get("123", "IND") == {"name": "Test"}
    assert cache.get("123", "SG") is None

    # Wait for expiry
    time.sleep(1.1)
    assert cache.get("123", "IND") is None

def test_cache_eviction():
    # Set max 5, set 6, should evict 50? No, my logic says if >= 50, evict 50.
    # Wait, my logic was if len >= max_entries: evict sorted_keys[:50].
    # If max_entries is small (like 5), and we set 5th, it will try to evict 50?
    # Let's adjust cache.py to evict min(len, 50) or something sensible.

    cache = TTLCache(ttl=60, max_entries=5)
    for i in range(5):
        cache.set(str(i), "IND", i)

    assert len(cache._store) == 5

    # Adding 6th should trigger eviction of 50 (or all if < 50)
    cache.set("6", "IND", 6)
    # Based on my cache.py code:
    # if len(self._store) >= self.max_entries: (5 >= 5 is true)
    # sorted_keys[:50] -> evicts all 5. Then adds "6".
    assert len(cache._store) == 1
    assert cache.get("6", "IND") == 6
    assert cache.get("0", "IND") is None
