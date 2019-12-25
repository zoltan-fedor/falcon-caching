API Reference Guide
===================


Cache API
---------

.. automodule:: falcon_caching
    :members:
    :inherited-members:
    :imported-members:


Backends
--------

.. module:: falcon_caching.backends

BaseCache
`````````

.. autoclass:: falcon_caching.backends.base.BaseCache
   :members:

NullCache
`````````

.. autoclass:: NullCache
   :members:

SimpleCache
```````````

.. autoclass:: SimpleCache
   :members:

FileSystemCache
```````````````

.. autoclass:: FileSystemCache
   :members:

RedisCache
``````````

.. autoclass:: Redis
   :members:

RedisSentinelCache
``````````````````

.. autoclass:: RedisSentinel
   :members:

UWSGICache
``````````

.. autoclass:: UWSGICache
   :members:

MemcachedCache
``````````````

.. autoclass:: MemcachedCache
   :members:

SASLMemcachedCache
``````````````````

.. autoclass:: SASLMemcachedCache
   :members:

SpreadSASLMemcachedCache
````````````````````````

.. autoclass:: SpreadSASLMemcachedCache
   :members:
