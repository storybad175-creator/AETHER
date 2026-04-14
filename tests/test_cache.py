import pytest
import asyncio
from core.cache import TTLCache
from api.schemas import PlayerData

@pytest.mark.asyncio
async def test_cache_hit():
    cache = TTLCache()
    uid, region = "123", "IND"
    data = MagicMock(spec=PlayerData)

    cache.set(uid, region, data)
    hit = cache.get(uid, region)
    assert hit == data

@pytest.mark.asyncio
async def test_cache_stampede_lock():
    cache = TTLCache()
    lock1 = await cache.get_lock("123", "IND")
    lock2 = await cache.get_lock("123", "IND")
    assert lock1 is lock2

from unittest.mock import MagicMock
