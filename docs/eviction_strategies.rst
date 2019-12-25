.. _eviction-strategies:

Eviction strategies
-------------------

Once a resource is cached, there is the question of how that cached record will be evicted
from the cache - alias what *'eviction strategy'* is followed.

Below is the list of supported strategies:

'time-based'
************
The most well known *eviction strategy* is simply *time-based*, meaning that the cached record
gets evicted based on a timeout (also called TTL, time-to-live) being reached. It this case
the cached data is invalidated x seconds after it was generated.
In our library this is called **'time-based'** eviction and it is the default *eviction
strategy*.

'rest-based'
************
For REST APIs - which implement the
`RESTful methods <https://en.wikipedia.org/wiki/Representational_state_transfer#Relationship_between_URI_and_HTTP_methods>`_
closely - there is another possible option, to evict records based on the definition of the
RESTful methods.

In this case GET requests are the only ones cached, but those are cached indefinitely.
They only get removed from the cache when another request
of the same resource of type PUT / PATCH / POST or DELETE arrives. This will
invalidate/evict the cached record and force the next GET request to re-cache it.
We call this **'rest-based'** eviction strategy.

'rest-and-time-based'
*********************
The third option is a combination of these two, where the eviction happens based on
whichever of these two events occurs first - the time expires or a PUT/PATCH/POST/DELETE
request arrives.
We call this **'rest-and-time-based'** eviction strategy.

These eviction strategies can be set with the **CACHE_EVICTION_STRATEGY** config attribute -
see :ref:`config-attributes`.

.. code-block:: python

    from falcon_caching import Cache

    cache = Cache(
        config={
            'CACHE_TYPE': 'simple',
            'CACHE_EVICTION_STRATEGY': 'rest-based'
        })
..

If no **CACHE_EVICTION_STRATEGY** is provided then the **'time-based'** strategy is used by default.
