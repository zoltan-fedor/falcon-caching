# -*- coding: utf-8 -*-
"""
    falcon_caching.async_backends.simple
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The simple cache backend (async).

    :copyright: (c) 2022 by Zoltan Fedor.
    :license: MIT, see LICENSE for more details.

    :copyright: (c) 2018 by Peter Justin.
    :copyright: (c) 2010 by Thadeus Burgess.
    :license: BSD, see LICENSE for more details.
"""
from time import time

from falcon_caching.async_backends.base import BaseCache

try:
    import cPickle as pickle
except ImportError:  # pragma: no cover
    import pickle  # type: ignore


class SimpleCache(BaseCache):
    """Simple memory cache for single process environments.  This class exists
    mainly for the development server and is not 100% thread safe.  It tries
    to use as many atomic operations as possible and no locks for simplicity
    but it could happen under heavy load that keys are added multiple times.

    :param threshold: the maximum number of items the cache stores before
                      it starts deleting some.
    :param default_timeout: the default timeout that is used if no timeout is
                            specified on :meth:`~BaseCache.set`. A timeout of
                            0 indicates that the cache never expires.
    :param ignore_errors: If set to ``True`` the :meth:`~BaseCache.delete_many`
                          method will ignore any errors that occured during the
                          deletion process. However, if it is set to ``False``
                          it will stop on the first error. Defaults to
                          ``False``.
    """

    def __init__(self, threshold=500, default_timeout=300, ignore_errors=False):
        super(SimpleCache, self).__init__(default_timeout)
        self._cache = {}
        self.clear = self._cache.clear
        self._threshold = threshold
        self.ignore_errors = ignore_errors

    async def _prune(self):
        if len(self._cache) > self._threshold:
            now = time()
            toremove = []
            for idx, (key, (expires, _)) in enumerate(self._cache.items()):
                if (expires != 0 and expires <= now) or idx % 3 == 0:
                    toremove.append(key)
            for key in toremove:
                self._cache.pop(key, None)

    async def _normalize_timeout(self, timeout):
        timeout = BaseCache._normalize_timeout(self, timeout)
        if timeout > 0:
            timeout = time() + timeout
        return timeout

    async def get(self, key):
        try:
            expires, value = self._cache[key]
            if expires == 0 or expires > time():
                return pickle.loads(value)
        except (KeyError, pickle.PickleError):
            return None

    async def set(self, key, value, timeout=None):
        expires = await self._normalize_timeout(timeout)
        await self._prune()
        self._cache[key] = (
            expires,
            pickle.dumps(value, pickle.HIGHEST_PROTOCOL),
        )
        return True

    async def add(self, key, value, timeout=None):
        expires = await self._normalize_timeout(timeout)
        await self._prune()
        item = (expires, pickle.dumps(value, pickle.HIGHEST_PROTOCOL))
        if key in self._cache:
            return False
        self._cache.setdefault(key, item)
        return True

    async def delete(self, key):
        return self._cache.pop(key, None) is not None

    async def has(self, key):
        try:
            expires, value = self._cache[key]
            return expires == 0 or expires > time()
        except KeyError:
            return False

    async def clear(self):
        return True
