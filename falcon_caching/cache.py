from inspect import isclass
from typing import Any, Dict, List, Optional

from falcon_caching.middleware import Middleware
from falcon_caching.options import CacheEvictionStrategy


class Cache:
    """ This is the central class for the caching

    You need to initialize this object to setup the attributes of the caching
    and then supply the object's middleware to the Falcon app.

    Args:
        config (dict of str: str): Cache config settings

    Attributes:
        cache (:obj:`BaseCache`): An initialized 'CACHE_TYPE' cache from the backends.
        cache_args (list of str): Optional list passed during the cache class instantiation.
        cache_options (dict of str: str): Optional dictionary passed during the cache class instantiation.
        config (dict of str: str): Cache config settings
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """ Import and initialize the cache object for the requested 'CACHE_TYPE'
        and set its arguments and options and then store it on self.cache """

        # set the defaults for the config
        config.setdefault("CACHE_DEFAULT_TIMEOUT", 300)
        config.setdefault("CACHE_IGNORE_ERRORS", False)
        config.setdefault("CACHE_THRESHOLD", 500)
        config.setdefault("CACHE_KEY_PREFIX", "flask_cache_")
        config.setdefault("CACHE_MEMCACHED_SERVERS", None)
        config.setdefault("CACHE_MEMCACHED_USERNAME", None)
        config.setdefault("CACHE_MEMCACHED_PASSWORD", None)
        config.setdefault("CACHE_DIR", None)
        config.setdefault("CACHE_OPTIONS", None)
        config.setdefault("CACHE_ARGS", [])
        config.setdefault("CACHE_TYPE", "null")
        config.setdefault("CACHE_NO_NULL_WARNING", False)
        config.setdefault("CACHE_EVICTION_STRATEGY", CacheEvictionStrategy.time_based)

        self.config = config

        import_me = config["CACHE_TYPE"]
        from . import backends
        try:
            cache_obj = getattr(backends, import_me)
        except AttributeError:
            raise ImportError(f"{import_me} is not a valid Falcon-Caching backend")

        self.cache_args = config["CACHE_ARGS"][:]
        self.cache_options = {"default_timeout": config["CACHE_DEFAULT_TIMEOUT"]}

        if config["CACHE_OPTIONS"]:
            self.cache_options.update(config["CACHE_OPTIONS"])

        # initialize the cache_object
        self.cache = cache_obj(self.config, self.cache_args, self.cache_options)

    @property
    def middleware(self) -> 'Middleware':
        """ Falcon middleware integration
        """
        return Middleware(self.cache, self.config)

    @staticmethod
    def cached(timeout: int):
        """ This is the decorator used to decorate a resource class or the requested
        method of the resource class
        """
        def wrap1(class_or_method, *args):
            # is this about decorating a class or a given method?
            if isclass(class_or_method):
                # get all methods of the class that needs to be decorated (eg start with "on_"):
                for attr in dir(class_or_method):
                    if callable(getattr(class_or_method, attr)) and attr.startswith("on_"):
                        # decorate the given method:
                        setattr(class_or_method, attr, wrap1(getattr(class_or_method, attr)))

                return class_or_method
            else:  # this is to decorate the individual method
                class_or_method.to_be_cached = True

                def cache_wrap(cls, req, resp, *args, **kwargs):
                    class_or_method(cls, req, resp, *args, **kwargs)
                    req.context['cache'] = True
                    req.context['cache_timeout'] = timeout

                return cache_wrap

        return wrap1

    def has(self, *args, **kwargs) -> bool:
        """It determines if the given key is in the cache."""
        _h = self.cache.has(*args, **kwargs)
        # the Redis backend returns 0 for not existing keys
        if isinstance(_h, bool):
            return _h
        elif isinstance(_h, int):
            return False if _h == 0 else True
        else:
            raise ValueError(f"has() returned an unknown value '{_h}'")

    def get(self, *args, **kwargs) -> Any:
        """It returns the value for the given key from the cache."""
        return self.cache.get(*args, **kwargs)

    def set(self, *args, **kwargs) -> bool:
        """It stores the given key and value in the cache."""
        return self.cache.set(*args, **kwargs)

    def add(self, *args, **kwargs) -> bool:
        """It adds a given key and value to the cache, but only
        if no record which such key already exists.
        """
        return self.cache.add(*args, **kwargs)

    def delete(self, *args, **kwargs) -> bool:
        """It deletes the cached record based on the provided key."""
        return self.cache.delete(*args, **kwargs)

    def delete_many(self, *args, **kwargs) -> bool:
        """It deletes all cached record matching the list of keys provided."""
        return self.cache.delete_many(*args, **kwargs)

    def clear(self) -> bool:
        """It clears all cache - if the `CACHE_KEY_PREFIX` config attribute
        is used then it only removes key starting with that prefix, otherwise
        it flushes the whole database."""
        return self.cache.clear()

    def get_many(self, *args, **kwargs) -> List[Any]:
        """It returns the list of values matching the list of keys."""
        return self.cache.get_many(*args, **kwargs)

    def set_many(self, *args, **kwargs) -> bool:
        """It stores multiple records based on the dictionary of keys
        and values provided."""
        return self.cache.set_many(*args, **kwargs)

    def get_dict(self, *args, **kwargs) -> Dict[Any, Any]:
        """It returns the keys and values as dictionary for all requested keys."""
        return self.cache.get_dict(*args, **kwargs)

    def inc(self, *args, **kwargs) -> Optional[int]:
        """It increments and returns the value of a numerical cache record.
        Only works for Redis and Redis Sentinel!
        """
        return self.cache.inc(*args, **kwargs)

    def dec(self, *args, **kwargs) -> Optional[int]:
        """It decrements and returns the value of a numerical cache record.
        Only works for Redis and Redis Sentinel!
        """
        return self.cache.dec(*args, **kwargs)
