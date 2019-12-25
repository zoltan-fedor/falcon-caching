Backends (alias 'CACHE_TYPE')
-----------------------------

When you are caching you have the choice of what kind of backend to
cache to, be that a Redis database, Memcached, the local process' memory
or just files on the local filesystem.

The Falcon-Caching library offers you different backend options and made to
be extendable, so additional backend options can be added.

The type of backend used is determined by the **CACHE_TYPE** attribute  -
see :ref:`config-attributes`.

Below is an example of using `CACHE_TYPE` with value `'simple'` - which makes
the cached records stored in the local process' memory (not 100% thread safe!):

.. code-block:: python

    from falcon_caching import Cache

    cache = Cache(
        config={
            'CACHE_TYPE': 'simple',  # backend 'simple' will be used
            'CACHE_EVICTION_STRATEGY': 'time-based'
        })
..

.. note::
    Credits must be given to the authors and maintainers of the
    `Flask-Caching <https://github.com/sh4nks/flask-caching>`_ library,
    as the structure and much of the code of our backends was ported from
    their popular library.

Below is a list of available backends, alias the available `CACHE_TYPE` options:


'simple'  (the default)
***********************

A simple memory cache for single process environments.  This option exists
mainly for the development server and is not 100% thread safe.  It tries
to use as many atomic operations as possible and no locks for simplicity,
but it could happen under heavy load that keys are added multiple times.
Do not use in production!

Example:

.. code-block:: python

    from falcon_caching import Cache

    cache = Cache(
        config={
            'CACHE_TYPE': 'simple',  # backend 'simple' will be used
            'CACHE_EVICTION_STRATEGY': 'time-based'
        })


'null'
******

A cache that doesn't cache.  This can be useful for unit testing.


'filesystem'
************

A cache that stores the items on the file system.  This cache depends
on being the only user of the '`cache_dir`'.  Make absolutely sure that
nobody but this cache stores files there or otherwise the cache will
randomly delete files therein.

Example:

.. code-block:: python

    from falcon_caching import Cache

    cache = Cache(
        config={
            'CACHE_TYPE': 'filesystem'
            'CACHE_EVICTION_STRATEGY': 'time-based',
            'CACHE_DIR': '/tmp/falcon-cache-dedicated/',
            'CACHE_THRESHOLD': 500  # the maximum number of items the
                                    # cache stores before it starts
                                    # deleting some. A threshold value
                                    # of 0 indicates no threshold.
                                    # default: 500
        })


'redis'
*******

A cache that stores the items in the Redis key-value store or an
object which is API compatible with the official Python Redis
client (`redis-py`).

If you want to use an object which is API compatible with the official
Python Redis client (`redis-py`), then just supply that initialized object
to the `CACHE_REDIS_HOST` parameter.

If you use the same Redis database for other purposes too, then you are strongly
advised to specify the `CACHE_KEY_PREFIX`, so keys would not accidentally collide
and `cache.clean()` calls would only remove keys from the cache and not other records.

Example:

.. code-block:: python

    from falcon_caching import Cache

    cache = Cache(
        config={
            'CACHE_TYPE': 'redis'
            'CACHE_EVICTION_STRATEGY': 'time-based',
            'CACHE_REDIS_HOST': 'localhost',  # Redis host/client object
                                              # default: 'localhost'
            'CACHE_REDIS_PORT': 6379,  # default: 6379
            'CACHE_REDIS_PASSWORD': 'MyRedisPassword',  # default: None
            'CACHE_REDIS_DB': 0,  # default: 0
            'CACHE_KEY_PREFIX': 'mycache'  # default: None
        })

Alternatively you could also supply a Redis URL via the CACHE_REDIS_URL argument,
like `redis://user:password@localhost:6379/2`.

'redis-sentinel'
****************

A cache that stores the items in a `Redis Sentinel <https://redis.io/topics/sentinel>`_,
which is a high availability 'load-balancer' for a Redis cluster.

Just like for 'redis', if you use the same Redis database for other purposes too,
then you are strongly
advised to specify the `CACHE_KEY_PREFIX`, so keys would not accidentally collide
and `cache.clean()` calls would only remove keys from the cache and not other records.

Example:

.. code-block:: python

    from falcon_caching import Cache

    cache = Cache(
        config={
            'CACHE_TYPE': 'redissentinel'
            'CACHE_EVICTION_STRATEGY': 'time-based',
            'CACHE_REDIS_SENTINELS': [("127.0.0.1", 26379),
                                     ("10.0.0.1", 26379)]
            'CACHE_REDIS_SENTINEL_MASTER': 'mymaster',  # default: None
            'CACHE_REDIS_PASSWORD': 'MyRedisPassword',  # default: None
            'CACHE_REDIS_SENTINEL_PASSWORD': 'MyPsw',   # default: None
            'CACHE_REDIS_DB': 0,  # default: 0
            'CACHE_KEY_PREFIX': 'mycache'  # default: None
        })


'memcached'
***********

A cache that stores the items in a Memcached instance or cluster.
It supports the `pylibmc`, `memcache` and the `google app engine memcache` libraries.

You can supply one ore more server addresses via `CACHE_MEMCACHED_SERVERS` or
you can supply an already initialized client, an object that resembles
the API of a `memcache.Client`. If you have a supplied server(s), then
the library will pick the best memcached client library available to use.

Example:

.. code-block:: python

    from falcon_caching import Cache

    cache = Cache(
        config={
            'CACHE_TYPE': 'memcached'
            'CACHE_EVICTION_STRATEGY': 'time-based',
            'CACHE_MEMCACHED_SERVERS': ["127.0.0.1:11211",
                                        "127.0.0.1:11212"]
            'CACHE_KEY_PREFIX': 'cache'  # default: None
        })

.. note:: Flask-Caching does not pass additional configuration options
   to memcached backends. To add additional configuration to these caches,
   directly set the configuration options on the object after instantiation::

    from falcon_caching import Cache

    cache = Cache(
        config={
            'CACHE_TYPE': 'memcached'
            'CACHE_EVICTION_STRATEGY': 'time-based',
            'CACHE_MEMCACHED_SERVERS': ["127.0.0.1:11211",
                                        "127.0.0.1:11212"]
            'CACHE_KEY_PREFIX': 'cache'  # default: None
        })

    # Break convention and set options on the _client object
    # directly. For pylibmc behaviors:
    cache.cache._client.behaviors["tcp_nodelay"] = True


'saslmemcached'
***************

A cache that stores the items in an SASL-authentication protected Memcached
instance or cluster.

Just like for `memcached` - you can supply one ore more server addresses
via `CACHE_MEMCACHED_SERVERS` or
you can supply an already initialized client, an object that resembles
the API of a `memcache.Client`.

Example:

.. code-block:: python

    from falcon_caching import Cache

    cache = Cache(
        config={
            'CACHE_TYPE': 'saslmemcached'
            'CACHE_EVICTION_STRATEGY': 'time-based',
            'CACHE_MEMCACHED_SERVERS': ["127.0.0.1:11211",
                                        "127.0.0.1:11212"]
            'CACHE_MEMCACHED_USERNAME': 'myuser',  # default: None
            'CACHE_MEMCACHED_PASSWORD': 'MyPassword',  # default: None
            'CACHE_KEY_PREFIX': 'cache'  # default: None
        })


'spreadsaslmemcached'
*********************

A subclass of the `saslmemcached` backend that will spread the cached values
across multiple records if they are bigger than the memcached treshold which
by default is 1M.

Spreading requires using `pickle` to store the value, which can significantly
impact the performance.


'uwsgi'
*******

Implements the cache using uWSGI's caching framework.

To set the uwsgi caching instance to connect to, for example: `mycache@localhost:3031`,
use the `CACHE_UWSGI_NAME` argument, which defaults to an empty string, in which case
uWSGI will cache in the local instance.

This backend cannot be used when running under PyPy, because the uWSGI
API implementation for PyPy is lacking the required functionality.


Example:

.. code-block:: python

    from falcon_caching import Cache

    cache = Cache(
        config={
            'CACHE_TYPE': 'uwsgi'
            'CACHE_UWSGI_NAME': 'mycache@localhost:3031',  # default: ''
            'CACHE_KEY_PREFIX': 'cache'  # default: None
        })
