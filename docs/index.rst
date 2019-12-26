Welcome to Falcon-Caching's documentation!
==========================================

Version: 0.1.1

Falcon-Caching adds cache support to the
`Falcon web framework <https://github.com/falconry/falcon>`_.

It is a port of the popular
`Flask-Caching <https://github.com/sh4nks/flask-caching>`_ library to Falcon.

The library aims to be compatible with CPython 3.6+ and PyPy 3.5+.

.. include:: quickstart.rst


Installation
------------

Install the extension with pip::

    $ pip install Falcon-Caching


Set Up
------

Cache is managed through a ``Cache`` instance::

    import falcon
    from falcon_caching import Cache

    # setup the cache instance
    cache = Cache(
        config=
        {
            'CACHE_EVICTION_STRATEGY': 'time-based',  # how records are
                                                      # evicted
            'CACHE_TYPE': 'simple'  # backend used to store the cache
        })

    class ThingsResource:
        # mark the method as cached for 600 seconds
        @cache.cached(timeout=600)
        def on_get(self, req, resp):
            pass

    # create the app with the cache middleware
    app = falcon.API(middleware=cache.middleware)

    things = ThingsResource()

    app.add_route('/things', things)

.. include:: eviction_strategies.rst

.. include:: backends.rst

.. include:: config.rst

.. _resource-level-caching:

Resource level caching
----------------------

In Falcon-Caching you mark individual methods or resources to be cached by adding the
``@cache.cached()`` decorator to them.

It is possible to add this decorator on the resource (class) level to mark the whole resource
- and so all of its ``'on_'`` methods - as cached:

.. code-block:: python

    # mark the whole resource as cached
    # which will decorate all the on_...() methods of this class
    @cache.cached(timeout=600)
    class ThingsResource:

        def on_get(self, req, resp):
            pass

        def on_post(self, req, resp):
            pass
..

BUT if any of those ``'on_'`` methods are supposed to modify the data or have some other
non-cachable actions,
then that will NOT be executed when the response is returned from the cache - assuming
the **CACHE_EVICTION_STRATEGY** is set to **'time-based'** - which is the default.

The **CACHE_EVICTION_STRATEGY** values of  **'rest-based'** and **'rest-and-time-based'** are safe,
as those invalidate the cache for any PUT/PATCH/POST/DELETE calls and do NOT serve the response
from the cache for those methods.

This happens because the `cache.middleware` short-circuits any further processing
**if a cached version of that item is found**.
If a cached version is found then it will skip any remaining `process_request` and
`process_resource` methods, as well as the `responder` method that the request would
have been routed to.
However, any `process_response` middleware methods will still be called.

We suggest that you only use the resource level (eg class) decorator if you use
the **CACHE_EVICTION_STRATEGY** of  **'rest-based'** or **'rest-and-time-based'** and NOT
if you use the **'time-based'** strategy. The only exception to this rule of thumb could be if
(1) you are certain that **all** the methods of that resource can be served from the cache or
(2) all the actions for those methods are taken in `process_response` phase.



Explicitly Caching Data
-----------------------

Data can be cached explicitly by using the proxy methods like
:meth:`Cache.set`, and :meth:`Cache.get` directly. There are many other proxy
methods available via the :class:`Cache` class - see them listed below.

For example:

.. code-block:: python

    from falcon_caching import Cache

    cache = Cache(
        config={
            'CACHE_TYPE': 'simple',
            'CACHE_EVICTION_STRATEGY': 'rest-based'
        })

    ...

    def test(foo=None):
        if foo is not None:
            cache.set("foo", foo)  # saving a value into the cache
        bar = cache.get("foo")  # retrieving the value from the cache


Supported methods:

.. code-block:: python


    cache.set("foo", "bar")
    cache.has("foo")
    cache.get("foo")
    cache.add("foo", "bar")  # like set, except it doesn't overwrite
    cache.set_many({"foo": "bar", "foo2": "bar2"})
    cache.get_many(["foo", "foo2"])  # returns a list
    cache.get_dict(["foo", "foo2"])  # returns a dict
    cache.delete("foo")
    cache.delete_many("foo", "foo2")
    cache.set("foo3", 1)
    cache.inc("foo3")  # increment, only supported by Redis&Redis Sentinel
    cache.dec("foo3")  # decrement, only supported by Redis&Redis Sentinel
    cache.clear()  # clears all cache - not supported by all backends
                   # WARNING: some implementations (Redis) will flush
                   # the whole database!!!

Query String
------------

Currently the `query string <https://falcon.readthedocs.io/en/stable/api/request_and_response.html#falcon.Request.query_string>`_
is NOT used in the cache key, so two requests which only differ in the query string will be cached
against the same key.

Development
-----------

For development guidelines see
`https://github.com/zoltan-fedor/falcon-caching#development <https://github.com/zoltan-fedor/falcon-caching#development>`_


.. _API Reference:

API Reference
-------------

If you are looking for information on a specific function, class or
method of a service, then this part of the documentation is for you.

.. toctree::
   :maxdepth: 2

   api_reference/index


Additional Information
----------------------

.. toctree::
   :maxdepth: 2

   changelog
   license

* :ref:`search`