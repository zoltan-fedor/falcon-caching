# -*- coding: utf-8 -*-
"""
    falcon_caching.async_backends.filesystem
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The filesystem caching backend.

    :copyright: (c) 2022 by Zoltan Fedor.
    :license: MIT, see LICENSE for more details.

    :copyright: (c) 2018 by Peter Justin.
    :copyright: (c) 2010 by Thadeus Burgess.
    :license: BSD, see LICENSE for more details.
"""
import aiofiles.os
import errno
import hashlib
import os
import tempfile
from time import time

from falcon_caching.async_backends.base import BaseCache

try:
    import cPickle as pickle
except ImportError:  # pragma: no cover
    import pickle


class FileSystemCache(BaseCache):

    """A cache that stores the items on the file system.  This cache depends
    on being the only user of the `cache_dir`.  Make absolutely sure that
    nobody but this cache stores files there or otherwise the cache will
    randomly delete files therein.

    :param cache_dir: the directory where cache files are stored.
    :param threshold: the maximum number of items the cache stores before
                      it starts deleting some. A threshold value of 0
                      indicates no threshold.
    :param default_timeout: the default timeout that is used if no timeout is
                            specified on :meth:`~BaseCache.set`. A timeout of
                            0 indicates that the cache never expires.
    :param mode: the file mode wanted for the cache files, default 0600
    :param hash_method: Default hashlib.md5. The hash method used to
                        generate the filename for cached results.
    :param ignore_errors: If set to ``True`` the :meth:`~BaseCache.delete_many`
                          method will ignore any errors that occured during the
                          deletion process. However, if it is set to ``False``
                          it will stop on the first error. Defaults to
                          ``False``.
    """

    #: used for temporary files by the FileSystemCache
    _fs_transaction_suffix = ".__wz_cache"
    #: keep amount of files in a cache element
    _fs_count_file = "__wz_cache_count"

    def __init__(
        self,
        cache_dir,
        threshold=500,
        default_timeout=300,
        mode=0o600,
        hash_method=hashlib.md5,
        ignore_errors=False,
    ):
        super().__init__(default_timeout)
        self._path = cache_dir
        self._threshold = threshold
        self._mode = mode
        self._hash_method = hash_method
        self.ignore_errors = ignore_errors

        try:
            os.makedirs(self._path)
        except OSError as ex:
            if ex.errno != errno.EEXIST:
                raise

        self._update_count(value=len(self._sync_list_dir()))

    def _file_count(self):
        return self.sync_get(self._fs_count_file) or 0

    def _update_count(self, delta=None, value=None):
        # If we have no threshold, don't count files
        if self._threshold == 0:
            return

        if delta:
            new_count = self._file_count() + delta
        else:
            new_count = value or 0
        self.sync_set(self._fs_count_file, new_count, mgmt_element=True)

    def _normalize_timeout(self, timeout):
        timeout = BaseCache._normalize_timeout(self, timeout)
        if timeout != 0:
            timeout = time() + timeout
        return int(timeout)

    def _sync_list_dir(self):
        """return a list of (fully qualified) cache filenames
        """
        mgmt_files = [
            self._get_filename(name).split("/")[-1]
            for name in (self._fs_count_file,)
        ]
        return [
            os.path.join(self._path, fn)
            # no support for listdir in aiofiles
            # see https://github.com/Tinche/aiofiles/issues/4
            for fn in os.listdir(self._path)
            if not fn.endswith(self._fs_transaction_suffix)
            and fn not in mgmt_files
        ]

    async def _list_dir(self):
        """return a list of (fully qualified) cache filenames
        """
        mgmt_files = [
            self._get_filename(name).split("/")[-1]
            for name in (self._fs_count_file,)
        ]
        return [
            os.path.join(self._path, fn)
            # no support for listdir in aiofiles
            # see https://github.com/Tinche/aiofiles/issues/4
            for fn in os.listdir(self._path)
            if not fn.endswith(self._fs_transaction_suffix)
            and fn not in mgmt_files
        ]

    async def _prune(self):
        if self._threshold == 0 or not self._file_count() > self._threshold:
            return

        entries = await self._list_dir()
        now = time()
        for idx, fname in enumerate(entries):
            try:
                remove = False
                async with aiofiles.open(fname, "rb") as f:
                    _expires = await f.read()

                expires = pickle.loads(_expires)
                remove = (expires != 0 and expires <= now) or idx % 3 == 0

                if remove:
                    await aiofiles.os.remove(fname)
            except (IOError, OSError):
                pass
        self._update_count(value=len(await self._list_dir()))

    async def clear(self):
        for fname in await self._list_dir():
            try:
                await aiofiles.os.remove(fname)
            except (IOError, OSError):
                self._update_count(value=len(await self._list_dir()))
                return False
        self._update_count(value=0)
        return True

    def _get_filename(self, key):
        if isinstance(key, str):
            key = key.encode("utf-8")  # XXX unicode review
        hash = self._hash_method(key).hexdigest()
        return os.path.join(self._path, hash)

    def sync_get(self, key):
        filename = self._get_filename(key)
        try:
            with open(filename, "rb") as f:
                pickle_time = pickle.load(f)
                if pickle_time == 0 or pickle_time >= time():
                    return pickle.load(f)
                else:
                    os.remove(filename)
                    return None
        except (IOError, OSError, pickle.PickleError):
            return None

    async def get(self, key):
        import io
        filename = self._get_filename(key)
        try:
            # this nasty thing is requried, because pickle cannot read files async
            # when the file contains multiple pickled object
            # see https://github.com/Tinche/aiofiles/issues/21#issuecomment-1025009415
            async with aiofiles.open(filename, "rb") as f:
                pickled_bytes = await f.read()

                with io.BytesIO() as f:
                    f.write(pickled_bytes)
                    f.seek(0)
                    pickle_time = pickle.load(f)

                    if pickle_time == 0 or pickle_time >= time():
                        return pickle.load(f)
                    else:
                        await aiofiles.os.remove(filename)
                        return None
        except (IOError, OSError, pickle.PickleError):
            # raise
            return None

    async def add(self, key, value, timeout=None):
        filename = self._get_filename(key)
        if not await aiofiles.os.path.exists(filename):
            return await self.set(key, value, timeout)
        return False

    def sync_set(self, key, value, timeout=None, mgmt_element=False):
        # Management elements have no timeout
        if mgmt_element:
            timeout = 0

        # Don't prune on management element update, to avoid loop
        else:
           self._prune()

        timeout = self._normalize_timeout(timeout)
        filename = self._get_filename(key)
        try:
            fd, tmp = tempfile.mkstemp(
                suffix=self._fs_transaction_suffix, dir=self._path
            )
            with os.fdopen(fd, "wb") as f:
                pickle.dump(timeout, f, 1)
                pickle.dump(value, f, pickle.HIGHEST_PROTOCOL)
            os.replace(tmp, filename)
            os.chmod(filename, self._mode)
        except (IOError, OSError):
            return False
        else:
            # Management elements should not count towards threshold
            if not mgmt_element:
                self._update_count(delta=1)
            return True

    async def set(self, key, value, timeout=None, mgmt_element=False):
        # Management elements have no timeout
        if mgmt_element:
            timeout = 0

        # Don't prune on management element update, to avoid loop
        else:
           await self._prune()

        timeout = self._normalize_timeout(timeout)
        filename = self._get_filename(key)
        try:
            fd, tmp = tempfile.mkstemp(
                suffix=self._fs_transaction_suffix, dir=self._path
            )
            async with aiofiles.open(fd, "wb") as f:
                await f.write(pickle.dumps(timeout, 1))
                await f.write(pickle.dumps(value, pickle.HIGHEST_PROTOCOL))
            await aiofiles.os.replace(tmp, filename)
            os.chmod(filename, self._mode)
        except (IOError, OSError):
            return False
        else:
            # Management elements should not count towards threshold
            if not mgmt_element:
                self._update_count(delta=1)
            return True

    async def delete(self, key, mgmt_element=False):
        try:
            await aiofiles.os.remove(self._get_filename(key))
        except (IOError, OSError):
            return False
        else:
            # Management elements should not count towards threshold
            if not mgmt_element:
                self._update_count(delta=-1)
            return True

    async def has(self, key):
        filename = self._get_filename(key)
        try:
            # read pickled file with aiofiles - see https://github.com/Tinche/aiofiles/issues/21#issuecomment-331111480
            async with aiofiles.open(filename, "rb") as f:
                _pickle_time = await f.read()

            pickle_time = pickle.loads(_pickle_time)

            if pickle_time == 0 or pickle_time >= time():
                return True
            else:
                await aiofiles.os.remove(filename)
                return False
        except (IOError, OSError, pickle.PickleError):
            return False
