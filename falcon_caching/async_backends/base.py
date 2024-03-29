# -*- coding: utf-8 -*-
"""
    falcon_caching.backends.base
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains the BaseCache that other caching
    backends have to implement.

    :copyright: (c) 2019 by Zoltan Fedor.
    :license: MIT, see LICENSE for more details.

    :copyright: (c) 2018 by Peter Justin.
    :copyright: (c) 2010 by Thadeus Burgess.
    :license: BSD, see LICENSE for more details.
"""


def iteritems_wrapper(mappingorseq):
    """Wrapper for efficient iteration over mappings represented by dicts
    or sequences::

        >>> for k, v in iteritems_wrapper((i, i*i) for i in xrange(5)):
        ...    assert k*k == v

        >>> for k, v in iteritems_wrapper(dict((i, i*i) for i in xrange(5))):
        ...    assert k*k == v

    """
    if hasattr(mappingorseq, "items"):
        return mappingorseq.items()
    return mappingorseq


class BaseCache(object):
    """Baseclass for the cache systems.  All the cache systems implement this
    API or a superset of it.

    :param default_timeout: The default timeout (in seconds) that is used if
                            no timeout is specified on :meth:`set`. A timeout
                            of 0 indicates that the cache never expires.
    """

    def __init__(self, default_timeout=300):
        self.default_timeout = default_timeout
        self.ignore_errors = False

    def _normalize_timeout(self, timeout):
        if timeout is None:
            timeout = self.default_timeout
        return timeout

    async def get(self, key):
        """Look up key in the cache and return the value for it.

        :param key: the key to be looked up.
        :returns: The value if it exists and is readable, else ``None``.
        """
        return None

    async def delete(self, key):
        """Delete `key` from the cache.

        :param key: the key to delete.
        :returns: Whether the key existed and has been deleted.
        :rtype: boolean
        """
        return True

    async def get_many(self, *keys):
        """Returns a list of values for the given keys.
        For each key an item in the list is created::

            foo, bar = cache.get_many("foo", "bar")

        Has the same error handling as :meth:`get`.

        :param keys: The function accepts multiple keys as positional
                     arguments.
        """
        return [await self.get(k) for k in keys]

    async def get_dict(self, *keys):
        """Like :meth:`get_many` but return a dict::

            d = cache.get_dict("foo", "bar")
            foo = d["foo"]
            bar = d["bar"]

        :param keys: The function accepts multiple keys as positional
                     arguments.
        """
        return dict(zip(keys, await self.get_many(*keys)))

    async def set(self, key, value, timeout=None):
        """Add a new key/value to the cache (overwrites value, if key already
        exists in the cache).

        :param key: the key to set
        :param value: the value for the key
        :param timeout: the cache timeout for the key in seconds (if not
                        specified, it uses the default timeout). A timeout of
                        0 indicates that the cache never expires.
        :returns: ``True`` if key has been updated, ``False`` for backend
                  errors. Pickling errors, however, will raise a subclass of
                  ``pickle.PickleError``.
        :rtype: boolean
        """
        return True

    async def add(self, key, value, timeout=None):
        """Works like :meth:`set` but does not overwrite the values of already
        existing keys.

        :param key: the key to set
        :param value: the value for the key
        :param timeout: the cache timeout for the key in seconds (if not
                        specified, it uses the default timeout). A timeout of
                        0 idicates that the cache never expires.
        :returns: Same as :meth:`set`, but also ``False`` for already
                  existing keys.
        :rtype: boolean
        """
        return True

    async def set_many(self, mapping, timeout=None):
        """Sets multiple keys and values from a mapping.

        :param mapping: a mapping with the keys/values to set.
        :param timeout: the cache timeout for the key in seconds (if not
                        specified, it uses the default timeout). A timeout of
                        0 idicates that the cache never expires.
        :returns: Whether all given keys have been set.
        :rtype: boolean
        """
        rv = True
        for key, value in iteritems_wrapper(mapping):
            if not await self.set(key, value, timeout):
                rv = False
        return rv

    async def delete_many(self, *keys):
        """Deletes multiple keys at once.

        :param keys: The function accepts multiple keys as positional
                     arguments.
        :returns: Whether all given keys have been deleted.
        :rtype: boolean
        """
        if self.ignore_errors:
            return all([await self.delete(key) for key in keys])
        return all([await self.delete(key) for key in keys])

    async def has(self, key):
        """Checks if a key exists in the cache without returning it. This is a
        cheap operation that bypasses loading the actual data on the backend.

        This method is optional and may not be implemented on all caches.

        :param key: the key to check
        """
        raise NotImplementedError(
            "%s doesn't have an efficient implementation of `has`. That "
            "means it is impossible to check whether a key exists without "
            "fully loading the key's data. Consider using `self.get` "
            "explicitly if you don't care about performance."
        )

    async def clear(self):
        """Clears the cache.  Keep in mind that not all caches support
        completely clearing the cache.

        :returns: Whether the cache has been cleared.
        :rtype: boolean
        """
        return True

    async def inc(self, key, delta=1):
        """Increments the value of a key by `delta`.  If the key does
        not yet exist it is initialized with `delta`.

        For supporting caches this is an atomic operation.

        :param key: the key to increment.
        :param delta: the delta to add.
        :returns: The new value or ``None`` for backend errors.
        """
        value = (await self.get(key) or 0) + delta
        return value if await self.set(key, value) else None

    async def dec(self, key, delta=1):
        """Decrements the value of a key by `delta`.  If the key does
        not yet exist it is initialized with `-delta`.

        For supporting caches this is an atomic operation.

        :param key: the key to increment.
        :param delta: the delta to subtract.
        :returns: The new value or `None` for backend errors.
        """
        value = (await self.get(key) or 0) - delta
        return value if await self.set(key, value) else None
