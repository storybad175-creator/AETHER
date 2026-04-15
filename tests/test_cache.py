import pytest
import asyncio
import time
from core.cache import TTLCache
from config.settings import settings

@pytest.mark.asyncio
async def test_cache_hit():
    cache = TTLCache()
    data = {"test": "data"}
    await cache.set("123", "IND", data)
    hit = await cache.get("123", "IND")
    assert hit == data

@pytest.mark.asyncio
async def test_cache_miss_expired():
    cache = TTLCache()
    data = {"test": "data"}
    # Manually set an expired timestamp
    await cache.set("123", "IND", data)
    cache._store[("123", "IND")]["expires_at"] = time.time() - 10

    miss = await cache.get("123", "IND")
    assert miss is None

@pytest.mark.asyncio
async def test_eviction():
    cache = TTLCache()
    settings.CACHE_MAX_ENTRIES = 5
    for i in range(6):
        await cache.set(str(i), "IND", {"i": i})

    # After adding 6th, it should evict 50 entries (or all in this small test)
    # Actually my logic evicts 50 or total.
    assert len(cache._store) <= 5
