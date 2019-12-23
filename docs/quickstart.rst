Quickstart
----------

.. code-block:: python

    import falcon
    from falcon_caching import Cache

    # setup the caching
    cache = Cache(config={'CACHE_TYPE': 'simple'})


    class ThingsResource:

        # mark the method as cached
        @cache.cached(timeout=600)
        def on_get(self, req, resp):
            pass


    # add the cache middleware
    app = falcon.API(middleware=cache.middleware)

    things = ThingsResource()

    app.add_route('/things', things)
..

Alternatively you could cache the whole resource (watch our for
issues mentioned in :ref:`resource-level-caching`):

.. code-block:: python

    # mark the whole resource as cached
    @cache.cached(timeout=600)
    class ThingsResource:

        def on_get(self, req, resp):
            pass

        def on_post(self, req, resp):
            pass
..

.. note::
    Be careful with the order of middlewares. The ``cache.middleware`` will
    short-circuit any further processing if a cached version of that resource is found.
    It will skip any remaining ``process_request`` and ``process_resource`` methods,
    as well as the ``responder`` method that the request would have been routed to.
    However, any ``process_response`` middleware methods will still be called.

    This is why it is suggested that you add the ``cache.middleware`` **following** any
    authentication / authorization middlewares to avoid unauthorized access of records
    served from the cache.


