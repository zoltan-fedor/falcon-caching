.. _config-attributes:

Configuring Falcon-Caching
--------------------------

The following configuration values exist for Falcon-Caching:

.. tabularcolumns:: |p{6.5cm}|p{8.5cm}|


=============================== ==================================================================
``CACHE_EVICTION_STRATEGY``     The `eviction strategy` determines when a cached
                                resource is removed from cache.

                                Available eviction strategies:

                                * **time-based**: records are removed once time expires (default)
                                * **rest-based**: records are removed once a PUT/POST/PATCH/DELETE call is made against the resource
                                * **rest-and-time-based**: records are removed either by time or request method (whichever happens first)

                                See more at :ref:`eviction-strategies`

``CACHE_TYPE``                  Specifies which type of caching object to
                                use. This is an import string that will
                                be imported and instantiated. It is
                                assumed that the import object is a
                                function that will return a cache
                                object that adheres to the cache API.

                                For falcon_caching.backends objects, you
                                do not need to specify the entire
                                import string, just one of the following
                                names.

                                Built-in cache types:

                                * **null**: NullCache (default)
                                * **simple**: SimpleCache
                                * **filesystem**: FileSystemCache
                                * **redis**: RedisCache (redis required)
                                * **redissentinel**: RedisSentinelCache (redis required)
                                * **uwsgi**: UWSGICache (uwsgi required)
                                * **memcached**: MemcachedCache (pylibmc or memcache required)
                                * **gaememcached**: same as memcached (for backwards compatibility)
                                * **saslmemcached**: SASLMemcachedCache (pylibmc required)
                                * **spreadsaslmemcached**: SpreadSASLMemcachedCache (pylibmc required)

``CACHE_NO_NULL_WARNING``       Silents the warning message when using
                                cache type of 'null'.
``CACHE_ARGS``                  Optional list to unpack and pass during
                                the cache class instantiation.
``CACHE_OPTIONS``               Optional dictionary to pass during the
                                cache class instantiation.
``CACHE_DEFAULT_TIMEOUT``       The default timeout that is used if no
                                timeout is specified. Unit of time is
                                seconds.
``CACHE_IGNORE_ERRORS``         If set to any errors that occurred during the
                                deletion process will be ignored. However, if
                                it is set to ``False`` it will stop on the
                                first error. This option is only relevant for
                                the backends **filesystem** and **simple**.
                                Defaults to ``False``.
``CACHE_THRESHOLD``             The maximum number of items the cache
                                will store before it starts deleting
                                some. Used only for SimpleCache and
                                FileSystemCache
``CACHE_KEY_PREFIX``            A prefix that is added before all keys.
                                This makes it possible to use the same
                                memcached server for different apps.
                                Used only for RedisCache and MemcachedCache
``CACHE_UWSGI_NAME``            The name of the uwsgi caching instance to
                                connect to, for example: mycache@localhost:3031,
                                defaults to an empty string, which means uWSGI
                                will cache in the local instance.
``CACHE_MEMCACHED_SERVERS``     A list or a tuple of server addresses.
                                Used only for MemcachedCache
``CACHE_MEMCACHED_USERNAME``    Username for SASL authentication with memcached.
                                Used only for SASLMemcachedCache
``CACHE_MEMCACHED_PASSWORD``    Password for SASL authentication with memcached.
                                Used only for SASLMemcachedCache
``CACHE_REDIS_HOST``            A Redis server host. Used only for RedisCache.
``CACHE_REDIS_PORT``            A Redis server port. Default is 6379.
                                Used only for RedisCache.
``CACHE_REDIS_PASSWORD``        A Redis password for server. Used only for RedisCache and
                                RedisSentinelCache.
``CACHE_REDIS_DB``              A Redis db (zero-based number index). Default is 0.
                                Used only for RedisCache and RedisSentinelCache.
``CACHE_REDIS_SENTINELS``       A list or a tuple of Redis sentinel addresses. Used only for
                                RedisSentinelCache.
``CACHE_REDIS_SENTINEL_MASTER`` The name of the master server in a sentinel configuration. Used
                                only for RedisSentinelCache.
``CACHE_DIR``                   Directory to store cache. Used only for
                                FileSystemCache.
``CACHE_REDIS_URL``             URL to connect to Redis server.
                                Example ``redis://user:password@localhost:6379/2``. Supports
                                protocols ``redis://``, ``rediss://`` (redis over TLS) and
                                ``unix://``. See more info about URL support at http://redis-py.readthedocs.io/en/latest/index.html#redis.ConnectionPool.from_url.
                                Used only for RedisCache.
=============================== ==================================================================
