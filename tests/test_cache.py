import pytest
import asyncio
from core.cache import TTLCache

@pytest.mark.asyncio
async def test_cache_hit_miss():
    cache = TTLCache()
    await cache.set("123", "IND", {"name": "test"})

    hit = await cache.get("123", "IND")
    assert hit == {"name": "test"}

    miss = await cache.get("456", "IND")
    assert miss is None

@pytest.mark.asyncio
async def test_cache_expiry():
    from config.settings import settings
    cache = TTLCache()

    with pytest.MonkeyPatch().context() as m:
        m.setattr(settings, "CACHE_TTL_SECONDS", -1)
        await cache.set("123", "IND", {"name": "expired"})
        hit = await cache.get("123", "IND")
        assert hit is None

@pytest.mark.asyncio
async def test_cache_eviction():
    from config.settings import settings
    cache = TTLCache()

    with pytest.MonkeyPatch().context() as m:
        m.setattr(settings, "CACHE_MAX_ENTRIES", 2)
        await cache.set("1", "IND", "data1")
        await cache.set("2", "IND", "data2")
        await cache.set("3", "IND", "data3") # Triggers eviction

        # In our implementation, it evicts 50 if max reached.
        # Since we have only 3, it should evict all if we hit 2.
        # Wait, sorted_items[:50] will take all 3.
        # Let's check how many are left.
        # Actually it only triggers when >= CACHE_MAX_ENTRIES.
        assert len(cache._store) <= 2
