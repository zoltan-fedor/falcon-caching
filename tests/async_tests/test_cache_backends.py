""" Test the cache backends using a raw Cache() object for each different
backed type.

Some of these tests were shamelessly taken from the Flask-Caching library -
just like the backends were.
"""
import os
import pytest
import random
import time

from tests.conftest import CACHE_THRESHOLD
from falcon_caching import AsyncCache
from falcon_caching.async_backends.memcache import (
    MemcachedCache,
    # SASLMemcachedCache,
    # SpreadSASLMemcachedCache
)
from falcon_caching.async_backends.redis import Redis, RedisSentinel


@pytest.mark.asyncio
async def test_cache_set(async_cache_time_based):
    cache = async_cache_time_based
    await cache.set("hi", "hello")
    assert await cache.has("hi") in [True, 1]
    assert await cache.has("nosuchkey") in [False, 0]
    assert await cache.get("hi") == "hello"


@pytest.mark.asyncio
async def test_cache_add(async_cache_time_based):
    cache = async_cache_time_based

    await cache.add("hi", "hello")
    assert await cache.get("hi") == "hello"

    await cache.add("hi", "foobar")
    assert await cache.get("hi") == "hello"


@pytest.mark.asyncio
async def test_cache_delete(async_cache_time_based):
    cache = async_cache_time_based
    await cache.set("hi", "hello")
    await cache.delete("hi")
    assert await cache.get("hi") is None


@pytest.mark.asyncio
async def test_cache_delete_many(async_cache_time_based):
    cache = async_cache_time_based
    await cache.set("hi", "hello")
    await cache.set("hi2", "hello")
    await cache.delete_many("hi", "hi2")
    assert await cache.get("hi") is None
    assert await cache.get("hi2") is None


@pytest.mark.asyncio
async def test_cache_unlink_if_not(async_cache_time_based):
    cache = async_cache_time_based
    # not every cache type has an unlink() method
    if hasattr(cache, 'unlink'):
        await cache.set("biggerkey", "test" * 100)
        await cache.unlink("biggerkey")
        assert await cache.get("biggerkey") is None

        await cache.set("biggerkey1", "test" * 100)
        await cache.set("biggerkey2", "test" * 100)
        await cache.unlink("biggerkey1", "biggerkey2")
        assert await cache.get("biggerkey1") is None
        assert await cache.get("biggerkey2") is None


@pytest.mark.asyncio
async def test_cache_delete_many_ignored():
    c = AsyncCache(config={"CACHE_TYPE": "simple", "CACHE_IGNORE_ERRORS": True, "EVICTION_STRATEGY": 'time-based'})
    cache = c.cache

    await cache.set("hi", "hello")
    assert await cache.get("hi") == "hello"
    await cache.delete_many("ho", "hi")
    assert await cache.get("hi") is None


@pytest.mark.asyncio
async def test_cache_pruning(async_cache_time_based):
    cache = async_cache_time_based
    """ Test that when adding more cache records than the threshold then
    some records get pruned, so the size of the cache stays at or below the threshold + 1
    """
    # for the Redis cache there is no pruning implemented, so we skip this test
    if isinstance(cache, Redis)\
            or isinstance(cache, RedisSentinel):
        pytest.skip("There is no pruning for Redis")

    # for the Memcache cache there is no pruning implemented, so we skip this test
    if isinstance(cache, MemcachedCache):
        pytest.skip("There is no pruning for Memcached")

    for i in range(CACHE_THRESHOLD + 5):
        await cache.set(f"hi-{i}", "hello")

    # the size of the cache is at or below the cache threshold:
    num_cached = 0
    for i in range(CACHE_THRESHOLD + 5):
        num_cached += 1 if await cache.has(f"hi-{i}") else 0

    assert num_cached <= CACHE_THRESHOLD + 1
