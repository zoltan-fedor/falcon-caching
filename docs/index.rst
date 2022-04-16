Welcome to Falcon-Caching's documentation!
==========================================

Version: 1.1.0

Falcon-Caching adds cache support to the
`Falcon web framework <https://github.com/falconry/falcon>`_.

It is a port of the popular
`Flask-Caching <https://github.com/sh4nks/flask-caching>`_ library to Falcon.

The library aims to be compatible with CPython 3.7+ and PyPy 3.5+.

You can use this library both with a sync (WSGI) or an async (ASGI) app,
by using the matching cache object (``Cache`` or ``AsyncCache``).
Throughout the documentation we will be mostly be showcasing examples
for the ``Cache`` object, but all those example could be used with the
``AsyncCache`` object too. The Quickstart example shows both ``Cache``
and ``AsyncCache`` side-by-side.
Obviously you should never be mixing the two in a single app, use
one or the other.

.. include:: quickstart.rst


Installation
------------

Install the extension with pip::

    $ pip install Falcon-Caching


Set Up
------

Cache is managed through a ``Cache`` and the ``AsyncCache`` instance::

    import falcon
    # import falcon.asgi
    from falcon_caching import Cache, AsyncCache

    # setup the cache instance
    cache = Cache(  # could also be 'AsyncCache'
        config=
        {
            'CACHE_EVICTION_STRATEGY': 'time-based',  # how records are
                                                      # evicted
            'CACHE_TYPE': 'simple'  # backend used to store the cache
        })

    class ThingsResource:
        # mark the method as cached for 600 seconds
        @cache.cached(timeout=600)
        def on_get(self, req, resp):   # this could also be an async function
            pass                       # if AsyncCache() is used

    # create the app with the cache middleware
    # you can use falcon.API() instead of falcon.App() below Falcon 3.0.0
    app = falcon.App(middleware=cache.middleware)
    # app = falcon.asgi.App(middleware=cache.middleware)


    things = ThingsResource()

    app.add_route('/things', things)

.. include:: eviction_strategies.rst

.. include:: backends.rst

.. _what_gets_cached:

What gets cached
----------------

You might ask the question that what (what data) is getting cached when a `responder`
is cached.

By default two things are cached: the ``response body`` and the response's ``Content-Type`` header.

To be able to store these two things in the cache backend under one object,
we use `msgpack <https://github.com/msgpack/msgpack-python>`_ to serialize and then deserialize
when loading the record back from the cache. While `msgpack` is a fast serializer, this does take
some time.

.. note::
    If you know that all of your cached responders are using the ```Content-Type`= `application/json```
    header - which is very typical for basic APIs in these days - then you don't need the
    ```Content-Type``` header to be cached.
    This is because the ```Content-Type` = `application/json``` is the default in Falcon and it is added
    to the response when no other value is specified.

    So in case your application only generates responses with the ```Content-Type` = `application/json``
    header, then you can turn off this serialization storing the ``Content-Type`` header and
    benefit from the performance boost of not needing to serialize and deserialize messages.

    You can turn off the serialization by setting **`CACHE_CONTENT_TYPE_JSON_ONLY = True`** in the config -
    see `Configuring Falcon-Caching`_.

.. versionadded:: 0.2


.. include:: memoization.rst


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


.. include:: recipes.rst


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