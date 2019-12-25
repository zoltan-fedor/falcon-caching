from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from falcon import API
    from falcon_caching.cache import Cache


def get_cache(app: 'API') -> 'Cache':
    """ Get the cache object from the app """
    return app._middleware[1][0].__self__


def get_cache_class(app: 'API'):
    """ Extracts the cache backend class from the Falcon app,
    so we can use it to determine when to skip certain tests
    """
    return get_cache(app).cache.__class__


def get_cache_eviction_strategy(app: 'API'):
    """ Extracts the cache eviction strategy from the Falcon app,
    so we can use it to determine when to skip certain tests
    """
    return get_cache(app).cache_config['CACHE_EVICTION_STRATEGY']


def delete_from_cache(app: 'API', path: str, method: str, request_body: str=None) -> None:
    """ Delete / remove a certain key from the cache
    """
    request_body = request_body if request_body else ''

    if path.endswith('/'):
        path = path[:-1]

    key = f'{path}:{method.upper()}:{request_body}'

    get_cache(app).cache.delete(key)
