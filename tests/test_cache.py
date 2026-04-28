import pytest
import asyncio
import time
from core.cache import TTLCache
from config.settings import settings

@pytest.mark.asyncio
async def test_cache_hit():
    cache = TTLCache()
    cache.set("123", "IND", {"data": "test"})

    assert cache.get("123", "IND") == {"data": "test"}

@pytest.mark.asyncio
async def test_cache_miss_expired():
    cache = TTLCache()
    # Temporarily shorten TTL
    original_ttl = settings.CACHE_TTL_SECONDS
    settings.CACHE_TTL_SECONDS = -1

    cache.set("123", "IND", {"data": "expired"})
    assert cache.get("123", "IND") is None

    settings.CACHE_TTL_SECONDS = original_ttl

@pytest.mark.asyncio
async def test_eviction():
    cache = TTLCache()
    # Temporarily shorten MAX_ENTRIES
    original_max = settings.CACHE_MAX_ENTRIES
    settings.CACHE_MAX_ENTRIES = 5

    for i in range(10):
        cache.set(str(i), "IND", {"val": i})

    assert len(cache._store) <= 5
    # The last one added should definitely be there
    assert cache.get("9", "IND") == {"val": 9}

    settings.CACHE_MAX_ENTRIES = original_max

@pytest.mark.asyncio
async def test_per_key_lock():
    cache = TTLCache()
    lock1 = await cache.get_lock("123", "IND")
    lock2 = await cache.get_lock("123", "IND")
    lock3 = await cache.get_lock("456", "IND")

    assert lock1 is lock2
    assert lock1 is not lock3
