from falcon import HTTP_200
from falcon_caching.options import CacheEvictionStrategy, HttpMethods
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from falcon_caching.cache import Cache


class Middleware:
    """ It integrates a cache object with Falcon by turning it into
    a Falcon Middleware
    """

    def __init__(self, cache: 'Cache', config: Dict[str, Any]) -> None:
        self.cache = cache
        self.cache_config = config

    def process_resource(self, req, resp, resource, params):
        """ Determine if the given request is marked for caching and if yes,
        then look it up in the cache and if found, then return the cached value
        """

        # Step 1: for 'rest-based' and 'rest&time-based' eviction strategies the
        # POST/PATCH/PUT/DELETE calls are never cached, they should never be
        # loaded from cache as they must always execute,
        # so for those we don't need to try to search the cache
        if self.cache_config['CACHE_EVICTION_STRATEGY'] in [CacheEvictionStrategy.rest_based,
                                                            CacheEvictionStrategy.rest_and_time_based] \
            and req.method.upper() in [HttpMethods.POST,
                                       HttpMethods.PATCH,
                                       HttpMethods.PUT,
                                       HttpMethods.DELETE]:
            return

        # Step 2: determine whether the given responder has caching setup
        # and if not then short-circuit to save on the lookup of request in the cache
        # as anyhow this request was not marked to be cached

        # find out which responder ("on_..." method) is going to be used to process this request
        responder = None
        for _method in dir(resource):
            if _method.startswith('on_') and _method[3:].upper() == req.method.upper():
                responder = _method
                break

        if responder:
            # get the name of the responder wrapper, which for cached objects is 'cache_wrap'
            # see the "Cache.cache" decorator in cache.py
            responder_wrapper_name = getattr(getattr(resource, responder), '__name__')

            if responder_wrapper_name != 'cache_wrap':
                # no caching was requested on this responder
                return

        # Step 3: look up the record in the cache
        key = self.generate_cache_key(req)
        data = self.cache.get(key)

        # "or self.cache.has(key)" was required, because 'data' can be None for one of two reasons:
        #   (1) - the given key wasn't cached yet
        #   (2) - the given key is cached, but the endpoint has returned None in its body
        # which is why if it is None then we also need to check for (2)
        if data or self.cache.has(key):
            resp.body = data
            resp.status = HTTP_200
            req.context['cached'] = True

            # Short-circuit any further processing to skip any remaining
            # 'process_request' and 'process_resource' methods, as well as
            # the 'responder' method that the request would have been routed to.
            # However, any 'process_response' middleware methods will still be called.
            resp.complete = True

    def process_response(self, req, resp, resource, req_succeeded):
        """ Cache the response if this request qualifies and has not been cached yet
        or for rest-based and rest-and-time-based evict the record from the cache if
        the request method is POST/PATCH/PUT or DELETE """

        # Step 1: for 'rest-based' and 'rest&time-based' eviction strategies the
        # POST/PATCH/PUT/DELETE calls are never cached and even more they
        # invalidate the record cached by the GET method
        if self.cache_config['CACHE_EVICTION_STRATEGY'] in [CacheEvictionStrategy.rest_based,
                                                            CacheEvictionStrategy.rest_and_time_based] \
            and req.method.upper() in [HttpMethods.POST,
                                       HttpMethods.PATCH,
                                       HttpMethods.PUT,
                                       HttpMethods.DELETE]:
            # get the cache key created by the GET method (assuming there was one)
            key = self.generate_cache_key(req, method='GET')
            self.cache.delete(key)
            return

        # Step 2: if it is marked to be cached, but has not yet been cached
        # then we cache it
        if 'cache' in req.context and req.context['cache'] \
                and ('cached' not in req.context or not req.context['cached']):
            key = self.generate_cache_key(req)
            value = resp.body

            # for the REST-based strategy there is no timeout, the cached record never expires
            if self.cache_config['CACHE_EVICTION_STRATEGY'] in [CacheEvictionStrategy.rest_based]:
                # timeout 0 - never expires
                timeout = 0
            else:
                # for the time-based and rest-and-time-based eviction strategy the
                # cached record expires
                timeout = req.context.get('cache_timeout', 600)

            self.cache.set(key, value, timeout=timeout)

    @staticmethod
    def generate_cache_key(req, method: str = None) -> str:
        """ Generate the cache key from the request using the path, method and request body """

        # Get the body of the request to be used in the key.
        # If Content-Length happens to be 0, or the header is
        # missing altogether, reading it as below will not block.
        # see https://falcon.readthedocs.io/en/stable/api/request_and_response.html#falcon.Request.stream
        request_body = req.stream.read(req.content_length or 0)
        request_body = request_body.decode() if request_body else ''

        path = req.path
        if path.endswith('/'):
            path = path[:-1]

        if not method:
            method = req.method

        return f'{path}:{method.upper()}:{request_body}'
