import pytest
import asyncio
from core.cache import TTLCache

@pytest.mark.asyncio
async def test_cache_set_get():
    cache = TTLCache()
    cache.set("123", "IND", {"name": "Test"})

    assert cache.get("123", "IND") == {"name": "Test"}
    assert cache.get("456", "IND") is None

@pytest.mark.asyncio
async def test_cache_expiry():
    cache = TTLCache()
    with patch("config.settings.settings.CACHE_TTL_SECONDS", 0):
        cache.set("123", "IND", {"name": "Test"})
        # Should be expired immediately
        assert cache.get("123", "IND") is None

from unittest.mock import patch

@pytest.mark.asyncio
async def test_cache_eviction():
    cache = TTLCache()
    with patch("config.settings.settings.CACHE_MAX_ENTRIES", 2):
        cache.set("1", "IND", "data1")
        cache.set("2", "IND", "data2")
        cache.set("3", "IND", "data3") # Should trigger eviction

        # Eviction removes 50 oldest, but here we only have 2, so it should remove all if limit is 2?
        # Actually our logic evicts min(50, len).
        # In this test case, after adding "3", len was 2, it evicts 2.
        # Wait, if len >= MAX, evict.
        # 1. set "1" (len 1)
        # 2. set "2" (len 2) -> len >= 2, evict 50 oldest. Store is empty. set "2".
        # 3. set "3" (len 2) -> len >= 2, evict. set "3".
        assert cache.get("1", "IND") is None
        assert cache.get("2", "IND") is None
        assert cache.get("3", "IND") is not None

@pytest.mark.asyncio
async def test_cache_stampede_prevention():
    cache = TTLCache()
    uid, region = "stampede", "IND"

    lock1 = await cache.get_lock(uid, region)
    lock2 = await cache.get_lock(uid, region)

    assert lock1 is lock2 # Same object

    async with lock1:
        # Simulate work
        await asyncio.sleep(0.1)
        cache.set(uid, region, "data")

    async with lock2:
        # Should get data immediately
        assert cache.get(uid, region) == "data"
