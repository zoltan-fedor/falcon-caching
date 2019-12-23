Introduction
============

We start by explaining some of the basics of caching to introduce
you to the options your will have in the Falcon-Caching library.

Backends
--------

When you are caching you have the choice of what kind of backend to
cache to, be that a Redis database, Memcached, the local process' memory
or just files on the local filesystem.

The Falcon-Caching library offers you different backend options and made to
be extendable, so additional backend options can be added in the future.

The type of backend used is determined by the **CACHE_TYPE** attribute (#TODO add link).

An example of using `CACHE_TYPE` `'simple'` - which makes the cached
records stored in the local process' memory:

.. code-block:: python

    from falcon_caching import Cache

    cache = Cache(
        config={
            'CACHE_TYPE': 'simple'
        })
..

.. note::
    Credits must be given to the authors and maintainers of the
    `Flask-Caching <https://github.com/sh4nks/flask-caching>`_ library,
    as the structure and much of the code of our backends was ported from
    their popular library.

Eviction strategies
-------------------

Once a resource is cached there is a question of how the cached record will be evicted
from the cache - alias what is the *eviction strategy*.

'time-based'
************
The most well known *eviction strategy* is simply *time-based*, meaning that the cached record
gets evicted based on a timeout (also called TTL, time-to-live) being reached, alias the cached
data is invalidated x seconds after it was generated.
In the Falcon-Caching library this is named **'time-based'** eviction and it is the default *eviction
strategy*.

'rest-based'
************
For REST APIs which implement the
`RESTful methods <https://en.wikipedia.org/wiki/Representational_state_transfer#Relationship_between_URI_and_HTTP_methods>`_
closely, there is another possible option - to evict records based on the definition of the
RESTful methods, namely that only GET requests are used to retrieve the record, but
those can be cached indefinitely,
while all other requests modify the record (PUT, PATCH, POST, DELETE) and so those would
invalidate/evict the cached record and force the next GET request to re-cache it.
We call this **'rest-based'** eviction strategy in our library.

'rest-and-time-based'
*********************
The third option is a combination of these two, where the eviction happens based on
whichever of these two events occurs first - the time expires or a PUT/PATCH/POST/DELETE
request arrives.
We call this **'rest-and-time-based'** eviction strategy.

These eviction strategies can be set with the **CACHE_EVICTION_STRATEGY** config attribute (#TODO add link).

.. code-block:: python

    from falcon_caching import Cache

    cache = Cache(
        config={
            'CACHE_TYPE': 'simple',
            'CACHE_EVICTION_STRATEGY': 'rest-based'
        })
..

If no **CACHE_EVICTION_STRATEGY** is provided then the **'time-based'** strategy is used by default.

.. _resource-level-caching:

Resource level caching
----------------------

In Falcon-Caching you mark individual methods or resources to be cached by adding the
``@cache.cached()`` decorator to them.

It is possible to add this decorator on the resource (class) level to mark the whole resource
- and so all of its ``'on_'`` methods as cached:

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
then that will NOT be applied when the response is returned from the cache - assuming
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
(1) you are certain that all the methods of that resource can be served from the cache or
(2) all the actions for those methods are taken in `process_response` phase.
