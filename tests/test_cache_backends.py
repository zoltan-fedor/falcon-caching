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
from falcon_caching import Cache
from falcon_caching.backends.memcache import (
    MemcachedCache,
    SASLMemcachedCache,
    SpreadSASLMemcachedCache
)
from falcon_caching.backends.redis import Redis, RedisSentinel


def test_cache_set(cache_time_based):
    cache = cache_time_based
    cache.set("hi", "hello")

    # on Travis the below fails for SpreadSASLMemcachedCache
    # but locally it doesn't...
    if not isinstance(cache, SpreadSASLMemcachedCache)\
            or os.getenv('TRAVIS', 'no') == 'no':
        assert cache.has("hi") in [True, 1]
        assert cache.has("nosuchkey") in [False, 0]

    assert cache.get("hi") == "hello"


def test_cache_add(cache_time_based):
    cache = cache_time_based
    # on Travis the below fails for SpreadSASLMemcachedCache
    # but locally it doesn't...
    if isinstance(cache, SpreadSASLMemcachedCache)\
            and os.getenv('TRAVIS', 'no') == 'yes':
        pytest.skip("Skipping for SpreadSASLMemcachedCache on Travis")

    cache.add("hi", "hello")
    assert cache.get("hi") == "hello"

    cache.add("hi", "foobar")
    assert cache.get("hi") == "hello"


def test_cache_delete(cache_time_based):
    cache = cache_time_based
    cache.set("hi", "hello")
    cache.delete("hi")
    assert cache.get("hi") is None


def test_cache_delete_many(cache_time_based):
    cache = cache_time_based
    cache.set("hi", "hello")
    cache.set("hi2", "hello")
    cache.delete_many("hi", "hi2")
    assert cache.get("hi") is None
    assert cache.get("hi2") is None


def test_cache_unlink_if_not(cache_time_based):
    cache = cache_time_based
    # not every cache type has an unlink() method
    if hasattr(cache, 'unlink'):
        cache.set("biggerkey", "test" * 100)
        cache.unlink("biggerkey")
        assert cache.get("biggerkey") is None

        cache.set("biggerkey1", "test" * 100)
        cache.set("biggerkey2", "test" * 100)
        cache.unlink("biggerkey1", "biggerkey2")
        assert cache.get("biggerkey1") is None
        assert cache.get("biggerkey2") is None


def test_cache_delete_many_ignored():
    c = Cache(config={"CACHE_TYPE": "simple", "CACHE_IGNORE_ERRORS": True, "EVICTION_STRATEGY": 'time-based'})
    cache = c.cache

    cache.set("hi", "hello")
    assert cache.get("hi") == "hello"
    cache.delete_many("ho", "hi")
    assert cache.get("hi") is None


def test_cache_pruning(cache_time_based):
    cache = cache_time_based
    """ Test that when adding more cache records than the threshold then
    some records get pruned, so the size of the cache stays at or below the threshold + 1
    """
    # for the Redis cache there is no pruning implemented, so we skip this test
    if isinstance(cache, Redis)\
            or isinstance(cache, RedisSentinel):
        pytest.skip("There is no pruning for Redis")

    # for the Memcache cache there is no pruning implemented, so we skip this test
    if isinstance(cache, MemcachedCache)\
            or isinstance(cache, SASLMemcachedCache)\
            or isinstance(cache, SpreadSASLMemcachedCache):
        pytest.skip("There is no pruning for Memcached")

    for i in range(CACHE_THRESHOLD + 5):
        cache.set(f"hi-{i}", "hello")

    # the size of the cache is at or below the cache threshold:
    num_cached = 0
    for i in range(CACHE_THRESHOLD + 5):
        num_cached += 1 if cache.has(f"hi-{i}") else 0

    assert num_cached <= CACHE_THRESHOLD + 1
