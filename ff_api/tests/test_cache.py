import pytest
import asyncio
import time
from ff_api.core.cache import TTLCache

@pytest.mark.asyncio
async def test_cache_hit():
    cache = TTLCache(ttl=10, max_entries=10)
    data = {"nickname": "Test"}
    cache.set("123", "IND", data)

    assert cache.get("123", "IND") == data

@pytest.mark.asyncio
async def test_cache_miss_expired():
    cache = TTLCache(ttl=-1, max_entries=10) # Expire immediately
    data = {"nickname": "Test"}
    cache.set("123", "IND", data)

    assert cache.get("123", "IND") is None

@pytest.mark.asyncio
async def test_eviction():
    cache = TTLCache(ttl=100, max_entries=5)
    for i in range(10):
        cache.set(str(i), "IND", {"i": i})

    # After setting 10 items in a 5-item cache with 50-item eviction minimum
    # Wait, our eviction is max(50, max_entries // 10) = 50.
    # So if we have 6 items, it will evict all of them since 50 > 6.
    assert len(cache._store) <= 5
