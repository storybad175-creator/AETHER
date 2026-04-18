import pytest
import asyncio
import time
from core.cache import TTLCache

@pytest.mark.asyncio
async def test_cache_hit():
    cache = TTLCache(ttl=10, max_entries=10)
    await cache.set("123", "IND", {"name": "Test"})

    data = await cache.get("123", "IND")
    assert data == {"name": "Test"}

@pytest.mark.asyncio
async def test_cache_miss_expired():
    cache = TTLCache(ttl=-1, max_entries=10) # Immediately expired
    await cache.set("123", "IND", {"name": "Test"})

    data = await cache.get("123", "IND")
    assert data is None

@pytest.mark.asyncio
async def test_eviction():
    cache = TTLCache(ttl=60, max_entries=5)
    for i in range(6):
        await cache.set(str(i), "IND", {"i": i})
        await asyncio.sleep(0.01) # Ensure different expires_at

    # Should have evicted 50 entries if > max,
    # but my implementation evicts 50 if len >= max.
    # With max=5, adding 6th should trigger eviction.
    # Since we only have 6, it will try to evict 50, effectively clearing it
    # except the one we just added.

    data = await cache.get("0", "IND")
    assert data is None
    data = await cache.get("5", "IND")
    assert data is not None
