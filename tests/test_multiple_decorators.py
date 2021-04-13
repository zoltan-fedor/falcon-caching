
from falcon import API, testing, HTTP_200, HTTP_429, HTTP_405
from falcon_caching.utils import register
import json
import pytest
import random
from time import sleep

from tests.conftest import EVICTION_STRATEGIES, FALCONVERSION_MAIN


def a_decorator(f):
    """ Just a random decorator for testing purposes
    """
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper


@pytest.mark.parametrize("eviction_strategy", [
    *EVICTION_STRATEGIES
])
def test_caching_multiple_decorators_on_method(caches, eviction_strategy):
    """ Testing caching when there are multiple decorators on the method
    """
    # get the cache for the given eviction strategy
    cache = caches[eviction_strategy]

    class CachedResource:
        # a resource where the cache is the first decorator
        @cache.cached(timeout=1)
        @a_decorator
        def on_get(self, req, resp):
            if FALCONVERSION_MAIN < 3:
                resp.body = json.dumps({'num': random.randrange(0, 100000)})
            else:
                resp.text = json.dumps({'num': random.randrange(0, 100000)})

    class CachedResource2:
        # a resource where the cache is NOT the first decorator
        @a_decorator
        @cache.cached(timeout=1)
        def on_get(self, req, resp):
            if FALCONVERSION_MAIN < 3:
                resp.body = json.dumps({'num': random.randrange(0, 100000)})
            else:
                resp.text = json.dumps({'num': random.randrange(0, 100000)})

    class CachedResource3:
        # a resource where the cache is NOT the first decorator, but the register() is used
        @register(a_decorator, cache.cached(timeout=1))
        def on_get(self, req, resp):
            if FALCONVERSION_MAIN < 3:
                resp.body = json.dumps({'num': random.randrange(0, 100000)})
            else:
                resp.text = json.dumps({'num': random.randrange(0, 100000)})

    app = API(middleware=cache.middleware)
    app.add_route('/randrange_cached', CachedResource())
    app.add_route('/randrange_cached2', CachedResource2())
    app.add_route('/randrange_cached3', CachedResource3())

    client = testing.TestClient(app)

    # scenario 1 - the cache is the first decorator
    result1 = client.simulate_get('/randrange_cached')
    result2 = client.simulate_get('/randrange_cached')
    assert result1.json['num'] == result2.json['num']

    # scenario 2 - the cache is NOT the first decorator - caching does NOT work!
    result1 = client.simulate_get('/randrange_cached2')
    result2 = client.simulate_get('/randrange_cached2')
    assert result1.json['num'] != result2.json['num']

    # scenario 3 - the cache is the NOT first decorator, but register() is used, so caching does work!
    result1 = client.simulate_get('/randrange_cached3')
    result2 = client.simulate_get('/randrange_cached3')
    assert result1.json['num'] == result2.json['num']
