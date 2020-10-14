
Recipes
=======

Multiple decorators
-------------------

For scenarios where there is a need for multiple decorators and the ``@cache.cached()`` cannot be the
topmost one, we need to register the decorators a special way.

This scenario is complicated because our ``@cache.cached()`` just marks the fact that the given
method is decorated with a cache, which later gets picked up by the middleware and triggers caching. If the
``@cache.cached()`` is the topmost
decorator then it is easy to pick that up, but if there are other decorators 'ahead' it, then those
will 'hide' the  ``@cache.cached()``. This is because decorators in Python are just syntactic sugar
for nested function calls.

To be able to tell if the given endpoint was decorated by the ``@cache.cached()`` decorator when that is NOT
the topmost decorator, you need to decorate your method by registering your decorators using the
``@register()`` helper decorator.

See more about this issue at
https://stackoverflow.com/questions/3232024/introspection-to-get-decorator-names-on-a-method


.. code-block:: python

    import falcon
    from falcon_caching import Cache
    from falcon_caching.utils import register

    limiter = Limiter(
        key_func=get_remote_addr,
        default_limits=["10 per hour", "2 per minute"]
    )

    cache = Cache(config={'CACHE_TYPE': 'simple'})

    class ThingsResource:
        # this is fine, as the @cache.cached() is the topmost (eg the first) decorator:
        @cache.cached(timeout=600)
        @another_decorator
        def on_get(self, req, resp):
            pass

    class ThingsResource2:
        # the @cache.cached() is NOT the topmost decorator, so
        # this would NOT work - the cache decorator would be ignored!!!!
        # DO NOT DO THIS:
        @another_decorator
        @cache.cached(timeout=600)
        def on_get(self, req, resp):
            pass

    class ThingsResource3:
        # use your decorators this way:
        @register(another_decorator, cache.cached(timeout=600))
        def on_get(self, req, resp):
            pass

..
