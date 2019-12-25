""" Functional tests to test an example app with the different
cache backends and eviction strategies
"""
import pytest
import time

from falcon_caching.backends.memcache import (
    MemcachedCache,
    SASLMemcachedCache,
    SpreadSASLMemcachedCache
)
from falcon_caching.backends.redis import Redis, RedisSentinel
from falcon_caching.backends.filesystem import FileSystemCache
from falcon_caching.backends.simple import SimpleCache
from tests.conftest import CACHE_EXPIRES, CACHE_BUSTING_METHODS
from tests.utils import get_cache, get_cache_class, get_cache_eviction_strategy,\
    delete_from_cache


def test_app_basic(client):
    # delete any existing cache records for this endpoint to ensure
    # that we start from scratch
    delete_from_cache(app=client.app, path='/randrange_cached', method="GET")
    result1 = client.simulate_get('/randrange_cached')
    assert 100000 >= result1.json['num'] >= 0


def test_onget_cache(client):
    """ Test a properly cached GET request
    """
    # delete any existing cache records for this endpoint to ensure
    # that we start from scratch
    delete_from_cache(app=client.app, path='/randrange_cached', method="GET")

    result1 = client.simulate_get('/randrange_cached')
    # if get_cache_class(client.app) in [SimpleCache, FileSystemCache]:
    #      pytest.skip("Skipping SimpleCache")

    result2 = client.simulate_get('/randrange_cached')

    assert result1.json['num'] == result2.json['num']


@pytest.mark.parametrize("decorator_type", [
    # testing the method-based decorators, eg calling the
    # /randrange_cached_expires endpoint
    ("method-decorated"),
    # testing the class-based decorators, eg calling the
    # /randrange_class_cached_expires endpoint
    ("class-decorated")
])
def test_cache_expires(client, decorator_type):
    """ Test expiring cache with the different eviction strategies both
    for method decorators and class decorators
    """
    if decorator_type == 'method-decorated':
        path = "/randrange_cached_expires"
    elif decorator_type == 'class-decorated':
        path = "/randrange_class_cached_expires"

    # delete any existing cache records for this endpoint to ensure
    # that we start from scratch
    delete_from_cache(app=client.app, path=path, method="GET")

    result1 = client.simulate_get(path)
    result2 = client.simulate_get(path)
    assert result1.json['num'] == result2.json['num']

    # if we wait long enough the cache expires so a new request will bring
    # a new value
    time.sleep(CACHE_EXPIRES)
    result3 = client.simulate_get(path)

    # if the eviction strategy is time-based or rest-and-time-based
    # then the cache should have already expired, so the request
    # should have gotten executed again
    eviction_strategy = get_cache_eviction_strategy(client.app)
    if eviction_strategy in ['time-based', 'rest-and-time-based']:
        assert result2.json['num'] != result3.json['num']
    elif eviction_strategy in ['rest-based']:
        assert result2.json['num'] == result3.json['num']

        # a POST command should evict the cache for rest-based
        client.simulate_post(path)

        result4 = client.simulate_get(path)
        assert result3.json['num'] != result4.json['num']


def test_rest_action_expires_cache(client):
    """ Test how cache records expires after different method requests
    with the different eviction strategies
    """
    # delete any existing cache records for this endpoint to ensure
    # that we start from scratch
    delete_from_cache(app=client.app, path="/randrange_cached", method="GET")
    for method in CACHE_BUSTING_METHODS:
        delete_from_cache(app=client.app, path="/randrange_cached", method=method)

    # normal get should chache for all eviction strategies
    result1 = client.simulate_get('/randrange_cached')
    result2 = client.simulate_get('/randrange_cached')
    assert result1.json['num'] == result2.json['num']

    eviction_strategy = get_cache_eviction_strategy(client.app)

    # if the eviction strategy is time-based then no request with
    # other method for the same endpoint should change that
    # but for the rest-based and rest-and-time-based it does change it
    if eviction_strategy == 'time-based':
        for method in CACHE_BUSTING_METHODS:
            result3 = client.simulate_get('/randrange_cached')

            # make the simulate_post(), simulate_put(), etc call:
            getattr(client, f"simulate_{method.lower()}")('/randrange_cached')

            result4 = client.simulate_get('/randrange_cached')
            assert result3.json['num'] == result4.json['num']

    elif eviction_strategy in ['rest-based', 'rest-and-time-based']:
        for method in CACHE_BUSTING_METHODS:
            result3 = client.simulate_get('/randrange_cached')

            # make the simulate_post(), simulate_put(), etc call:
            getattr(client, f"simulate_{method.lower()}")('/randrange_cached')

            result4 = client.simulate_get('/randrange_cached')
            assert result3.json['num'] != result4.json['num']


def test_explicit_caching(caches):
    """ Testing of explicit caching and retrieving of records
    """
    # it is sufficient to test it with one type of cache
    cache = caches['time-based']

    # delete the 'foo21' record to be sure that it is not left in the cache
    cache.delete_many("foo21", "foo22", "foo23", "foo24", "foo25")

    assert cache.has("foo21") is False

    cache.set("foo21", "bar")
    assert cache.has("foo21") is True

    # add() does not overwrite existing keys
    cache.add("foo21", "bar2")
    assert cache.get("foo21") == 'bar'

    # for SpreadSASLMemcachedCache the add() doesn't work
    if cache.cache.__class__ not in [SpreadSASLMemcachedCache]:
        cache.add("foo22", "bar2")
    else:
        cache.set("foo22", "bar2")
    assert cache.get("foo22") == 'bar2'

    # for SpreadSASLMemcachedCache the add() doesn't work
    if cache.cache.__class__ not in [SpreadSASLMemcachedCache]:
        assert cache.get_many("foo21", "foo22") == ["bar", "bar2"]
        assert cache.get_dict("foo21", "foo22") == {"foo21": "bar", "foo22": "bar2"}

    cache.set_many({"foo23": "bar3", "foo24": "bar4"})
    assert cache.get_many("foo23", "foo24") == ["bar3", "bar4"]

    # for SpreadSASLMemcachedCache the add() doesn't work
    if cache.cache.__class__ not in [SpreadSASLMemcachedCache]:
        cache.delete_many("foo21", "foo22")
        assert cache.has("foo21") is False
        assert cache.has("foo22") is False

        assert cache.has("foo23") is True
        assert cache.has("foo24") is True
        cache.clear()
        assert cache.has("foo23") is False
        assert cache.has("foo24") is False

    # these only work for Redis
    if cache.cache.__class__ in [Redis, RedisSentinel]:
        cache.set("foo25", 1)
        cache.inc("foo25")
        assert cache.get("foo25") == 2

        cache.dec("foo25")
        assert cache.get("foo25") == 1
