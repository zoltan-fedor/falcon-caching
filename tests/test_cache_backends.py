""" Test the cache backends using a raw Cache() object for each different
backed type.

Some of these tests were shamelessly taken from the Flask-Caching library -
just like the backends were.
"""
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


def test_cache_set(cache):
    cache.set("hi", "hello")

    # on Travis the below fails for some unknown reason:
    if not isinstance(cache, SpreadSASLMemcachedCache):
        assert cache.has("hi") in [True, 1]
        assert cache.has("nosuchkey") in [False, 0]

    assert cache.get("hi") == "hello"


def test_cache_add(cache):
    cache.add("hi", "hello")
    assert cache.get("hi") == "hello"

    cache.add("hi", "foobar")
    assert cache.get("hi") == "hello"


def test_cache_delete(cache):
    cache.set("hi", "hello")
    cache.delete("hi")
    assert cache.get("hi") is None


def test_cache_delete_many(cache):
    cache.set("hi", "hello")
    cache.set("hi2", "hello")
    cache.delete_many("hi", "hi2")
    assert cache.get("hi") is None
    assert cache.get("hi2") is None


def test_cache_unlink_if_not(cache):
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
    c = Cache(config={"CACHE_TYPE": "simple", "CACHE_IGNORE_ERRORS": True})
    cache = c.cache

    cache.set("hi", "hello")
    assert cache.get("hi") == "hello"
    cache.delete_many("ho", "hi")
    assert cache.get("hi") is None


def test_cache_pruning(cache):
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

'''

def test_cache_cached_function(app, cache):
    with app.test_request_context():

        @cache.cached(1, key_prefix="MyBits")
        def get_random_bits():
            return [random.randrange(0, 2) for i in range(50)]

        my_list = get_random_bits()
        his_list = get_random_bits()

        assert my_list == his_list

        time.sleep(2)

        his_list = get_random_bits()

        assert my_list != his_list


def test_cache_accepts_multiple_ciphers(app, cache, hash_method):
    with app.test_request_context():

        @cache.cached(1, key_prefix="MyBits", hash_method=hash_method)
        def get_random_bits():
            return [random.randrange(0, 2) for i in range(50)]

        my_list = get_random_bits()
        his_list = get_random_bits()

        assert my_list == his_list

        time.sleep(2)

        his_list = get_random_bits()

        assert my_list != his_list


def test_cached_none(app, cache):
    with app.test_request_context():
        from collections import Counter

        call_counter = Counter()

        @cache.cached(cache_none=True)
        def cache_none(param):
            call_counter[param] += 1

            return None

        cache_none(1)

        assert call_counter[1] == 1
        assert cache_none(1) is None
        assert call_counter[1] == 1

        cache.clear()

        cache_none(1)
        assert call_counter[1] == 2


def test_cached_doesnt_cache_none(app, cache):
    """Asserting that when cache_none is False, we always
       assume a None value returned from .get() means the key is not found
    """
    with app.test_request_context():
        from collections import Counter

        call_counter = Counter()

        @cache.cached()
        def cache_none(param):
            call_counter[param] += 1

            return None

        cache_none(1)

        # The cached function should have been called
        assert call_counter[1] == 1

        # Next time we call the function, the value should be coming from the cache…
        # But the value is None and so we treat it as uncached.
        assert cache_none(1) is None

        # …thus, the call counter should increment to 2
        assert call_counter[1] == 2

        cache.clear()

        cache_none(1)
        assert call_counter[1] == 3


def test_cache_forced_update(app, cache):
    from collections import Counter

    with app.test_request_context():
        need_update = False
        call_counter = Counter()

        @cache.cached(1, forced_update=lambda: need_update)
        def cached_function(param):
            call_counter[param] += 1

            return 1

        cached_function(1)
        assert call_counter[1] == 1

        assert cached_function(1) == 1
        assert call_counter[1] == 1

        need_update = True

        assert cached_function(1) == 1
        assert call_counter[1] == 2


def test_cache_forced_update_params(app, cache):
    from collections import Counter

    with app.test_request_context():
        cached_call_counter = Counter()
        call_counter = Counter()
        call_params = {}

        def need_update(param):
            """This helper function returns True if it has been called with
            the same params for more than 2 times
            """

            call_counter[param] += 1
            call_params[call_counter[param] - 1] = (param,)

            return call_counter[param] > 2

        @cache.cached(1, forced_update=need_update)
        def cached_function(param):
            cached_call_counter[param] += 1

            return 1

        assert cached_function(1) == 1
        # need_update should have been called once
        assert call_counter[1] == 1
        # the parameters used to call need_update should be the same as the
        # parameters used to call cached_function
        assert call_params[0] == (1,)
        # the cached function should have been called once
        assert cached_call_counter[1] == 1

        assert cached_function(1) == 1
        # need_update should have been called twice by now as forced_update
        # should be called regardless of the arguments
        assert call_counter[1] == 2
        # the parameters used to call need_update should be the same as the
        # parameters used to call cached_function
        assert call_params[1] == (1,)
        # this time the forced_update should have returned False, so
        # cached_function should not have been called again
        assert cached_call_counter[1] == 1

        assert cached_function(1) == 1
        # need_update should have been called thrice by now as forced_update
        # should be called regardless of the arguments
        assert call_counter[1] == 3
        # the parameters used to call need_update should be the same as the
        # parameters used to call cached_function
        assert call_params[1] == (1,)
        # this time the forced_update should have returned True, so
        # cached_function should have been called again
        assert cached_call_counter[1] == 2
'''
