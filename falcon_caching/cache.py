"""
    falcon_caching.cache
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains the main Cache class and memoization-related methods.
    The latter is sourced from the Flask-Caching module.

    :copyright: (c) 2020 by Zoltan Fedor.
    :license: MIT, see LICENSE for more details.

    :copyright: (c) 2010 by Thadeus Burgess.
    :license: BSD, see LICENSE for more details.
"""
import base64
from collections import OrderedDict
import functools
import hashlib
import inspect
import logging
import string
import uuid
from typing import Any, Dict, List, Optional

from falcon_caching.middleware import Middleware, _DECORABLE_METHOD_NAME
from falcon_caching.options import CacheEvictionStrategy


TEMPLATE_FRAGMENT_KEY_TEMPLATE = "_template_fragment_cache_%s%s"
SUPPORTED_HASH_FUNCTIONS = [
    hashlib.sha1,
    hashlib.sha224,
    hashlib.sha256,
    hashlib.sha384,
    hashlib.sha512,
    hashlib.md5,
]

logger = logging.getLogger(__name__)

# Used to remove control characters and whitespace from cache keys.
valid_chars = set(string.ascii_letters + string.digits + "_.")
delchars = "".join(c for c in map(chr, range(256)) if c not in valid_chars)
null_control = (dict((k, None) for k in delchars),)


def wants_args(f):
    """Check if the function wants any arguments
    """
    argspec = inspect.getfullargspec(f)
    return bool(argspec.args or argspec.varargs or argspec.varkw)


def get_arg_names(f):
    """Return arguments of function
    :param f:
    :return: String list of arguments
    """
    sig = inspect.signature(f)
    return [
        parameter.name
        for parameter in sig.parameters.values()
        if parameter.kind == parameter.POSITIONAL_OR_KEYWORD
    ]


def get_arg_default(f, position):
    sig = inspect.signature(f)
    arg = list(sig.parameters.values())[position]
    arg_def = arg.default
    return arg_def if arg_def != inspect.Parameter.empty else None


def get_id(obj):
    return getattr(obj, "__caching_id__", repr)(obj)


def function_namespace(f, args=None):
    """Attempts to returns unique namespace for function"""
    m_args = get_arg_names(f)

    instance_token = None

    instance_self = getattr(f, "__self__", None)

    if instance_self and not inspect.isclass(instance_self):
        instance_token = get_id(f.__self__)
    elif m_args and m_args[0] == "self" and args:
        instance_token = get_id(args[0])

    module = f.__module__

    if m_args and m_args[0] == "cls" and not inspect.isclass(args[0]):
        raise ValueError(
            "When using `delete_memoized` on a "
            "`@classmethod` you must provide the "
            "class as the first argument"
        )

    if hasattr(f, "__qualname__"):
        name = f.__qualname__
    else:
        klass = getattr(f, "__self__", None)

        if klass and not inspect.isclass(klass):
            klass = klass.__class__

        if not klass:
            klass = getattr(f, "im_class", None)

        if not klass:
            if m_args and args:
                if m_args[0] == "self":
                    klass = args[0].__class__
                elif m_args[0] == "cls":
                    klass = args[0]

        if klass:
            name = klass.__name__ + "." + f.__name__
        else:
            name = f.__name__

    ns = ".".join((module, name))
    ns = ns.translate(*null_control)

    if instance_token:
        ins = ".".join((module, name, instance_token))
        ins = ins.translate(*null_control)
    else:
        ins = None

    return ns, ins


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
        config.setdefault("CACHE_KEY_PREFIX", "falcon_cache_")
        config.setdefault("CACHE_MEMCACHED_SERVERS", None)
        config.setdefault("CACHE_MEMCACHED_USERNAME", None)
        config.setdefault("CACHE_MEMCACHED_PASSWORD", None)
        config.setdefault("CACHE_DIR", None)
        config.setdefault("CACHE_OPTIONS", None)
        config.setdefault("CACHE_ARGS", [])
        config.setdefault("CACHE_TYPE", "null")
        config.setdefault("CACHE_NO_NULL_WARNING", False)
        config.setdefault("CACHE_EVICTION_STRATEGY", CacheEvictionStrategy.time_based)
        config.setdefault("CACHE_CONTENT_TYPE_JSON_ONLY", False)
        config.setdefault("CACHE_DEBUG", False)

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
            if inspect.isclass(class_or_method):
                # get all methods of the class that needs to be decorated (eg start with "on_"):
                for attr in dir(class_or_method):
                    if callable(getattr(class_or_method, attr)) and _DECORABLE_METHOD_NAME.match(attr):
                        setattr(class_or_method, attr, wrap1(getattr(class_or_method, attr)))

                return class_or_method
            else:  # this is to decorate the individual method
                class_or_method.to_be_cached = True

                def cache_wrap(cls, req, resp, *args, **kwargs):
                    class_or_method(cls, req, resp, *args, **kwargs)
                    req.context.cache = True
                    req.context.cache_timeout = timeout

                return cache_wrap

        # this is the name which will check for if the decorator was registered with the register()
        # function, as this decorator is not the topmost one
        wrap1._decorator_name = 'cache'  # type: ignore

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

    def _memvname(self, funcname):
        return funcname + "_memver"

    def _memoize_make_version_hash(self):
        return base64.b64encode(uuid.uuid4().bytes)[:6].decode("utf-8")

    def _memoize_version(
        self,
        f,
        args=None,
        kwargs=None,
        reset=False,
        delete=False,
        timeout=None,
        forced_update=False,
    ):
        """Updates the hash version associated with a memoized function or
        method.
        """
        fname, instance_fname = function_namespace(f, args=args)
        version_key = self._memvname(fname)
        fetch_keys = [version_key]

        if instance_fname:
            instance_version_key = self._memvname(instance_fname)
            fetch_keys.append(instance_version_key)

        # Only delete the per-instance version key or per-function version
        # key but not both.
        if delete:
            self.cache.delete_many(fetch_keys[-1])
            return fname, None

        version_data_list = list(self.cache.get_many(*fetch_keys))
        dirty = False

        if (
            callable(forced_update)
            and (
                forced_update(*(args or ()), **(kwargs or {}))
                if wants_args(forced_update)
                else forced_update()
            )
            is True
        ):
            # Mark key as dirty to update its TTL
            dirty = True

        if version_data_list[0] is None:
            version_data_list[0] = self._memoize_make_version_hash()
            dirty = True

        if instance_fname and version_data_list[1] is None:
            version_data_list[1] = self._memoize_make_version_hash()
            dirty = True

        # Only reset the per-instance version or the per-function version
        # but not both.
        if reset:
            fetch_keys = fetch_keys[-1:]
            version_data_list = [self._memoize_make_version_hash()]
            dirty = True

        if dirty:
            self.cache.set_many(
                dict(zip(fetch_keys, version_data_list)), timeout=timeout
            )

        return fname, "".join(version_data_list)

    def _memoize_make_cache_key(
        self,
        make_name=None,
        timeout=None,
        forced_update=False,
        hash_method=hashlib.md5,
    ):
        """Function used to create the cache_key for memoized functions."""

        def make_cache_key(f, *args, **kwargs):
            _timeout = getattr(timeout, "cache_timeout", timeout)
            fname, version_data = self._memoize_version(
                f, args=args, timeout=_timeout, forced_update=forced_update
            )

            #: this should have to be after version_data, so that it
            #: does not break the delete_memoized functionality.
            altfname = make_name(fname) if callable(make_name) else fname

            if callable(f):
                keyargs, keykwargs = self._memoize_kwargs_to_args(
                    f, *args, **kwargs
                )
            else:
                keyargs, keykwargs = args, kwargs

            updated = u"{0}{1}{2}".format(altfname, keyargs, keykwargs)

            cache_key = hash_method()
            cache_key.update(updated.encode("utf-8"))
            cache_key = base64.b64encode(cache_key.digest())[:16]
            cache_key = cache_key.decode("utf-8")
            cache_key += version_data

            return cache_key

        return make_cache_key

    def _memoize_kwargs_to_args(self, f, *args, **kwargs):
        #: Inspect the arguments to the function
        #: This allows the memoization to be the same
        #: whether the function was called with
        #: 1, b=2 is equivilant to a=1, b=2, etc.
        new_args = []
        arg_num = 0

        # If the function uses VAR_KEYWORD type of parameters,
        # we need to pass these further
        kw_keys_remaining = list(kwargs.keys())
        arg_names = get_arg_names(f)
        args_len = len(arg_names)

        for i in range(args_len):
            arg_default = get_arg_default(f, i)
            if i == 0 and arg_names[i] in ("self", "cls"):
                #: use the id func of the class instance
                #: this supports instance methods for
                #: the memoized functions, giving more
                #: flexibility to developers
                arg = get_id(args[0])
                arg_num += 1
            elif arg_names[i] in kwargs:
                arg = kwargs[arg_names[i]]
                kw_keys_remaining.pop(kw_keys_remaining.index(arg_names[i]))
            elif arg_num < len(args):
                arg = args[arg_num]
                arg_num += 1
            elif arg_default:
                arg = arg_default
                arg_num += 1
            else:
                arg = None
                arg_num += 1

            #: Attempt to convert all arguments to a
            #: hash/id or a representation?
            #: Not sure if this is necessary, since
            #: using objects as keys gets tricky quickly.
            # if hasattr(arg, '__class__'):
            #     try:
            #         arg = hash(arg)
            #     except:
            #         arg = get_id(arg)

            #: Or what about a special __cacherepr__ function
            #: on an object, this allows objects to act normal
            #: upon inspection, yet they can define a representation
            #: that can be used to make the object unique in the
            #: cache key. Given that a case comes across that
            #: an object "must" be used as a cache key
            # if hasattr(arg, '__cacherepr__'):
            #     arg = arg.__cacherepr__

            new_args.append(arg)

        new_args.extend(args[len(arg_names):])
        return (
            tuple(new_args),
            OrderedDict(
                sorted(
                    (k, v) for k, v in kwargs.items() if k in kw_keys_remaining
                )
            ),
        )

    def _bypass_cache(self, unless, f, *args, **kwargs):
        """Determines whether or not to bypass the cache by calling unless().
        Supports both unless() that takes in arguments and unless()
        that doesn't.
        """
        bypass_cache = False

        if callable(unless):
            argspec = inspect.getfullargspec(unless)
            has_args = len(argspec.args) > 0 or argspec.varargs or argspec.varkw

            # If unless() takes args, pass them in.
            if has_args:
                if unless(f, *args, **kwargs) is True:
                    bypass_cache = True
            elif unless() is True:
                bypass_cache = True

        return bypass_cache

    def memoize(
        self,
        timeout=None,
        make_name=None,
        unless=None,
        forced_update=None,
        response_filter=None,
        hash_method=hashlib.md5,
        cache_none=False,
    ):
        """Use this to cache the result of a function, taking its arguments
        into account in the cache key.
        Information on
        `Memoization <http://en.wikipedia.org/wiki/Memoization>`_.
        Example::
            @cache.memoize(timeout=50)
            def big_foo(a, b):
                return a + b + random.randrange(0, 1000)

        ::
            >>> big_foo(5, 2)
            753
            >>> big_foo(5, 3)
            234
            >>> big_foo(5, 2)
            753
            The returned decorated function now has three function attributes
            assigned to it.
                **uncached**
                    The original undecorated function. readable only
                **cache_timeout**
                    The cache timeout value for this function.
                    For a custom value to take affect, this must be
                    set before the function is called.
                    readable and writable
                **make_cache_key**
                    A function used in generating the cache_key used.
                    readable and writable

        :param timeout: Default None. If set to an integer, will cache for that
                        amount of time. Unit of time is in seconds.
        :param make_name: Default None. If set this is a function that accepts
                          a single argument, the function name, and returns a
                          new string to be used as the function name.
                          If not set then the function name is used.
        :param unless: Default None. Cache will *always* execute the caching
                       facilities unless this callable is true.
                       This will bypass the caching entirely.
        :param forced_update: Default None. If this callable is true,
                              cache value will be updated regardless cache
                              is expired or not. Useful for background
                              renewal of cached functions.
        :param response_filter: Default None. If not None, the callable is
                                invoked after the cached funtion evaluation,
                                and is given one arguement, the response
                                content. If the callable returns False, the
                                content will not be cached. Useful to prevent
                                caching of code 500 responses.
        :param hash_method: Default hashlib.md5. The hash method used to
                            generate the keys for cached results.
        :param cache_none: Default False. If set to True, add a key exists
                           check when cache.get returns None. This will likely
                           lead to wrongly returned None values in concurrent
                           situations and is not recommended to use.
        """
        if not timeout:
            timeout = self.cache_options["default_timeout"]

        def memoize(f):
            @functools.wraps(f)
            def decorated_function(*args, **kwargs):
                #: bypass cache
                if self._bypass_cache(unless, f, *args, **kwargs):
                    return f(*args, **kwargs)

                try:
                    cache_key = decorated_function.make_cache_key(
                        f, *args, **kwargs
                    )

                    if (
                        callable(forced_update)
                        and (
                            forced_update(*args, **kwargs)
                            if wants_args(forced_update)
                            else forced_update()
                        )
                        is True
                    ):
                        rv = None
                        found = False
                    else:
                        rv = self.cache.get(cache_key)
                        found = True

                        # If the value returned by cache.get() is None, it
                        # might be because the key is not found in the cache
                        # or because the cached value is actually None
                        if rv is None:
                            # If we're sure we don't need to cache None values
                            # (cache_none=False), don't bother checking for
                            # key existence, as it can lead to false positives
                            # if a concurrent call already cached the
                            # key between steps. This would cause us to
                            # return None when we shouldn't
                            if not cache_none:
                                found = False
                            else:
                                found = self.cache.has(cache_key)
                except Exception:
                    if self.config['CACHE_DEBUG']:
                        raise
                    logger.exception("Exception possibly due to cache backend.")
                    return f(*args, **kwargs)

                if not found:
                    rv = f(*args, **kwargs)

                    if response_filter is None or response_filter(rv):
                        try:
                            self.cache.set(
                                cache_key,
                                rv,
                                timeout=decorated_function.cache_timeout,
                            )
                        except Exception:
                            if self.config['CACHE_DEBUG']:
                                raise
                            logger.exception(
                                "Exception possibly due to cache backend."
                            )
                return rv

            decorated_function.uncached = f
            decorated_function.cache_timeout = timeout
            decorated_function.make_cache_key = self._memoize_make_cache_key(
                make_name=make_name,
                timeout=decorated_function,
                forced_update=forced_update,
                hash_method=hash_method,
            )
            decorated_function.delete_memoized = lambda: self.delete_memoized(f)

            return decorated_function

        return memoize

    def delete_memoized(self, f, *args, **kwargs):
        """Deletes the specified functions caches, based by given parameters.
        If parameters are given, only the functions that were memoized
        with them will be erased. Otherwise all versions of the caches
        will be forgotten.
        Example::
            @cache.memoize(50)
            def random_func():
                return random.randrange(1, 50)
            @cache.memoize()
            def param_func(a, b):
                return a+b+random.randrange(1, 50)

        ::
            >>> random_func()
            43
            >>> random_func()
            43
            >>> cache.delete_memoized(random_func)
            >>> random_func()
            16
            >>> param_func(1, 2)
            32
            >>> param_func(1, 2)
            32
            >>> param_func(2, 2)
            47
            >>> cache.delete_memoized(param_func, 1, 2)
            >>> param_func(1, 2)
            13
            >>> param_func(2, 2)
            47

        Delete memoized is also smart about instance methods vs class methods.
        When passing a instancemethod, it will only clear the cache related
        to that instance of that object. (object uniqueness can be overridden
        by defining the __repr__ method, such as user id).
        When passing a classmethod, it will clear all caches related across
        all instances of that class.
        Example::
            class Adder(object):
                @cache.memoize()
                def add(self, b):
                    return b + random.random()

        ::
            >>> adder1 = Adder()
            >>> adder2 = Adder()
            >>> adder1.add(3)
            3.23214234
            >>> adder2.add(3)
            3.60898509
            >>> cache.delete_memoized(adder1.add)
            >>> adder1.add(3)
            3.01348673
            >>> adder2.add(3)
            3.60898509
            >>> cache.delete_memoized(Adder.add)
            >>> adder1.add(3)
            3.53235667
            >>> adder2.add(3)
            3.72341788

        :param fname: The memoized function.
        :param \*args: A list of positional parameters used with
                       memoized function.
        :param \**kwargs: A dict of named parameters used with
                          memoized function.

        .. note::
            Falcon-Caching uses inspect to order kwargs into positional args when
            the function is memoized. If you pass a function reference into
            ``fname``, Falcon-Caching will be able to place the args/kwargs in
            the proper order, and delete the positional cache.
            However, if ``delete_memoized`` is just called with the name of the
            function, be sure to pass in potential arguments in the same order
            as defined in your function as args only, otherwise Falcon-Caching
            will not be able to compute the same cache key and delete all
            memoized versions of it.
        .. note::
            Falcon-Caching maintains an internal random version hash for
            the function. Using delete_memoized will only swap out
            the version hash, causing the memoize function to recompute
            results and put them into another key.
            This leaves any computed caches for this memoized function within
            the caching backend.
            It is recommended to use a very high timeout with memoize if using
            this function, so that when the version hash is swapped, the old
            cached results would eventually be reclaimed by the caching
            backend.
        """
        if not callable(f):
            raise TypeError(
                "Deleting messages by relative name is not supported, please "
                "use a function reference."
            )

        if not (args or kwargs):
            self._memoize_version(f, reset=True)
        else:
            cache_key = f.make_cache_key(f.uncached, *args, **kwargs)
            self.cache.delete(cache_key)

    def delete_memoized_verhash(self, f, *args):
        """Delete the version hash associated with the function.
        .. warning::
            Performing this operation could leave keys behind that have
            been created with this version hash. It is up to the application
            to make sure that all keys that may have been created with this
            version hash at least have timeouts so they will not sit orphaned
            in the cache backend.
        """
        if not callable(f):
            raise TypeError(
                "Deleting messages by relative name is not supported, please"
                "use a function reference."
            )

        self._memoize_version(f, delete=True)
