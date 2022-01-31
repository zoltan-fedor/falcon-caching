# -*- coding: utf-8 -*-
"""
    flask_caching.async_backends.memcache
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The memcache caching backend.

    :copyright: (c) 2022 by Zoltan Fedor.
    :license: MIT, see LICENSE for more details.

    :copyright: (c) 2018 by Peter Justin.
    :copyright: (c) 2010 by Thadeus Burgess.
    :license: BSD, see LICENSE for more details.
"""
import re
from time import time

from falcon_caching.async_backends.base import BaseCache, iteritems_wrapper

try:
    import cPickle as pickle
except ImportError:  # pragma: no cover
    import pickle

try:
    import emcache
except ImportError:  # pragma: no cover
    pass


_test_memcached_key = re.compile(r"[^\x00-\x21\xff]{1,250}$").match


class MemcachedCache(BaseCache):

    """A cache that uses memcached as backend.

    The first argument is a tuple/list of server addresses. It will try to import the best
    available memcache library.

    This cache looks into the following packages/modules to find bindings for
    memcached:

        - ``emcache``

    Implementation notes:  This cache backend works around some limitations in
    memcached to simplify the interface.  For example unicode keys are encoded
    to utf-8 on the fly.  Methods such as :meth:`~BaseCache.get_dict` return
    the keys in the same format as passed.  Furthermore all get methods
    silently ignore key errors to not cause problems when untrusted user data
    is passed to the get methods which is often the case in web applications.

    :param servers: a list or tuple of server addresses (server and port)
    :param default_timeout: the default timeout that is used if no timeout is
                            specified on :meth:`~BaseCache.set`. A timeout of
                            0 indicates that the cache never expires.
    :param key_prefix: a prefix that is added before all keys.  This makes it
                       possible to use the same memcached server for different
                       applications.  Keep in mind that
                       :meth:`~BaseCache.clear` will also clear keys with a
                       different prefix.
    """

    def __init__(self, servers=None, default_timeout=300, key_prefix=None, **options):
        super(MemcachedCache, self).__init__(default_timeout)

        self._servers = ["127.0.0.1:11211"] if servers is None else servers

        self._default_timeout = default_timeout
        self._options = options

        # populated later async
        self._client = None

        self.key_prefix = key_prefix or None

    async def get_client(self):
        if not self._client:
            try:
                import emcache
            except ImportError:
                raise RuntimeError("no emcache module found")

            _servers = []
            for s in self._servers:
                _host = s.split(":")[0]
                _port = int(s.split(":")[1])
                _servers.append(emcache.MemcachedHostAddress(_host, _port))

            self._client = await emcache.create_client(node_addresses=_servers,
                                                       timeout=self._default_timeout,
                                                       **self._options)

        return self._client

    def _normalize_key(self, key):
        key = str(key)
        if self.key_prefix:
            key = self.key_prefix + key
        return key

    def _normalize_timeout(self, timeout):
        timeout = BaseCache._normalize_timeout(self, timeout)
        if timeout > 0:
            timeout = int(time()) + timeout

        return timeout

    def _encode_key(self, key):
        """ emcache expect the keys to be provided as bytes and not as strings """
        return key.encode() if isinstance(key, str) else key

    def _decode_key(self, key):
        """ emcache returns keys as bytes """
        return key if not key or isinstance(key, str) else key.decode()

    def _encode_value(self, value):
        """ Encode a value which will be sent to memcached to bytes """
        return pickle.dumps(value)

    def _decode_value(self, value):
        """ Decode a value recived from memcached (which is an Items object with a
         pickled 'value' attribute) from bytes """
        return pickle.loads(value.value) if value else value

    async def get(self, key):
        key = self._normalize_key(key)
        # memcached doesn't support keys longer than that.  Because often
        # checks for so long keys can occur because it's tested from user
        # submitted data etc we fail silently for getting.
        if _test_memcached_key(key):
            return self._decode_value(await (await self.get_client()).get(self._encode_key(key)))

    async def get_dict(self, *keys):
        key_mapping = {}
        have_encoded_keys = True
        for key in keys:
            encoded_key = self._normalize_key(key)
            if _test_memcached_key(key):
                key_mapping[self._encode_key(encoded_key)] = self._encode_key(key)
        _keys = list(key_mapping)
        d = rv = await (await self.get_client()).get_many(_keys)
        if have_encoded_keys or self.key_prefix:
            rv = {}
            for key, value in d.items():
                rv[key_mapping[self._encode_key(key)]] = value
        if len(rv) < len(keys):
            for key in keys:
                if key not in rv:
                    rv[key] = None
        # # decode the list of dict where the keys are bytes and the values are Item objects
        # # with pickled values into a normal dict of values
        return {self._decode_key(k): self._decode_value(v) for k, v in rv.items()}

    async def add(self, key, value, timeout=None):
        key = self._normalize_key(key)
        timeout = self._normalize_timeout(timeout)
        try:
            return await (await self.get_client()).add(self._encode_key(key), self._encode_value(value), exptime=timeout)
        except emcache.client_errors.NotStoredStorageCommandError:
            # the key already exists in memcached
            return False

    async def set(self, key, value, timeout=None):
        key = self._normalize_key(key)
        timeout = self._normalize_timeout(timeout)
        return await (await self.get_client()).set(self._encode_key(key), self._encode_value(value), exptime=timeout)

    async def get_many(self, *keys):
        d = await self.get_dict(*keys)
        return [d[key] for key in keys]

    async def set_many(self, mapping, timeout=None):
        for key, value in mapping.items():
            await self.set(key, value, timeout)

        # no 'set_multi' in emcache, see https://github.com/emcache/emcache#usage
        # timeout = self._normalize_timeout(timeout)
        # failed_keys = await (await self.get_client()).set_multi(new_mapping, timeout)
        return True

    async def delete(self, key):
        _key = self._normalize_key(key)
        if _test_memcached_key(_key):
            if await self.has(key):
                return await (await self.get_client()).delete(self._encode_key(_key))
            else:
                return True

    async def delete_many(self, *keys):
        for key in keys:
            _key = self._normalize_key(key)
            if _test_memcached_key(_key):
                await self.delete(key)
        return True

    async def has(self, key):
        _key = self._normalize_key(key)
        if _test_memcached_key(_key):
            return not (not await self.get(key))
        return False

    async def clear(self):
        return await (await self.get_client()).flush_all()

    async def inc(self, key, delta=1):
        key = self._normalize_key(key)
        return await (await self.get_client()).increment(self._encode_key(key), delta)

    async def dec(self, key, delta=1):
        key = self._normalize_key(key)
        return await (await self.get_client()).decrement(self._encode_key(key), delta)


class SASLMemcachedCache(MemcachedCache):
    def __init__(
        self,
        servers=None,
        default_timeout=300,
        key_prefix=None,
        username=None,
        password=None,
        **kwargs
    ):
        raise RuntimeError("Sorry, the emcache library does not support SASL (binary protocol), "
                           "see https://github.com/emcache/emcache/issues/59.")


class SpreadSASLMemcachedCache(SASLMemcachedCache):
    """Simple Subclass of SASLMemcached client that will spread the value
    across multiple keys if they are bigger than a given treshold.

    Spreading requires using pickle to store the value, which can significantly
    impact the performance.
    """

    def __init__(self, *args, **kwargs):
        """
        Kwargs:
            chunksize (int): max length of a pickled object that can fit in
                memcached (memcache has an upper limit of 1MB for values,
                default: 1048448)
        """
        super(SpreadSASLMemcachedCache, self).__init__(*args, **kwargs)
