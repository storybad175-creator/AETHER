import pytest
import asyncio
from core.cache import TTLCache
from unittest.mock import patch

@pytest.mark.asyncio
async def test_cache_set_get():
    cache = TTLCache()
    cache.set("123", "IND", {"name": "Test"})

    assert cache.get("123", "IND") == {"name": "Test"}
    assert cache.get("456", "IND") is None

@pytest.mark.asyncio
async def test_cache_expiry():
    cache = TTLCache()
    with patch("config.settings.settings.CACHE_TTL_SECONDS", -1):
        cache.set("123", "IND", {"name": "Test"})
        # Should be expired immediately
        assert cache.get("123", "IND") is None

@pytest.mark.asyncio
async def test_cache_eviction():
    cache = TTLCache()
    # Set limit to 2
    with patch("config.settings.settings.CACHE_MAX_ENTRIES", 2):
        cache.set("1", "IND", "data1") # Store: {1}
        cache.set("2", "IND", "data2") # Store: {1, 2}

        # This should trigger eviction because len(store) >= 2
        cache.set("3", "IND", "data3")

        # Based on my eviction logic, it evicts 10% or at least 1.
        # len=2, num_to_evict = max(1, 0.2) = 1.
        # Key "1" was added first, so it has smaller expiry time.
        assert cache.get("1", "IND") is None
        assert cache.get("2", "IND") == "data2"
        assert cache.get("3", "IND") == "data3"
