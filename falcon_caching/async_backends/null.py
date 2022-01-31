# -*- coding: utf-8 -*-
"""
    flask_caching.async_backends.null
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    The null cache backend. A caching backend that doesn't cache.
    :copyright: (c) 2018 by Peter Justin.
    :copyright: (c) 2010 by Thadeus Burgess.
    :license: BSD, see LICENSE for more details.
"""
from falcon_caching.async_backends.base import BaseCache


class NullCache(BaseCache):
    """A cache that doesn't cache.  This can be useful for unit testing.

    :param default_timeout: a dummy parameter that is ignored but exists
                            for API compatibility with other caches.
    """

    async def has(self, key):
        return False
