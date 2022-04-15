from falcon_caching.async_backends.filesystem import FileSystemCache
from falcon_caching.async_backends.memcache import (
    MemcachedCache,
    SASLMemcachedCache,
    SpreadSASLMemcachedCache
)
from falcon_caching.async_backends.null import NullCache
from falcon_caching.async_backends.redis import Redis, RedisSentinel
from falcon_caching.async_backends.simple import SimpleCache

__all__ = (
    "null",
    "simple",
    "filesystem",
    "redis",
    "redissentinel",
    "uwsgi",
    "memcached",
    "gaememcached",
    "saslmemcached",
    "spreadsaslmemcached",
)


def null(config, args, kwargs):
    return NullCache()


def simple(config, args, kwargs):
    kwargs.update(
        dict(
            threshold=config["CACHE_THRESHOLD"],
            ignore_errors=config["CACHE_IGNORE_ERRORS"],
        )
    )
    return SimpleCache(*args, **kwargs)


def filesystem(config, args, kwargs):
    args.insert(0, config["CACHE_DIR"])
    kwargs.update(
        dict(
            threshold=config["CACHE_THRESHOLD"],
            ignore_errors=config["CACHE_IGNORE_ERRORS"],
        )
    )
    return FileSystemCache(*args, **kwargs)


def redis(config, args, kwargs):
    try:
        from coredis import Redis as _Redis
        redis_from_url = _Redis.from_url
    except ImportError:
        raise RuntimeError("no coredis module found")

    kwargs.update(
        dict(
            host=config.get("CACHE_REDIS_HOST", "localhost"),
            port=config.get("CACHE_REDIS_PORT", 6379),
        )
    )
    password = config.get("CACHE_REDIS_PASSWORD")
    if password:
        kwargs["password"] = password

    key_prefix = config.get("CACHE_KEY_PREFIX")
    if key_prefix:
        kwargs["key_prefix"] = key_prefix

    db_number = config.get("CACHE_REDIS_DB")
    if db_number:
        kwargs["db"] = db_number

    redis_url = config.get("CACHE_REDIS_URL")
    if redis_url:
        kwargs["host"] = redis_from_url(redis_url, db=kwargs.pop("db", None))

    return Redis(*args, **kwargs)


def redissentinel(config, args, kwargs):
    kwargs.update(
        dict(
            sentinels=config.get(
                "CACHE_REDIS_SENTINELS", [("127.0.0.1", 26379)]
            ),
            master=config.get("CACHE_REDIS_SENTINEL_MASTER", "mymaster"),
            password=config.get("CACHE_REDIS_PASSWORD", None),
            sentinel_password=config.get("CACHE_REDIS_SENTINEL_PASSWORD", None),
            key_prefix=config.get("CACHE_KEY_PREFIX", None),
            db=config.get("CACHE_REDIS_DB", 0),
        )
    )

    return RedisSentinel(*args, **kwargs)


def uwsgi(config, args, kwargs):
    raise NotImplementedError(
        "UWSGICache backend is not available in async!"
    )


def memcached(config, args, kwargs):
    args.append(config["CACHE_MEMCACHED_SERVERS"])
    kwargs.update(dict(key_prefix=config["CACHE_KEY_PREFIX"]))
    return MemcachedCache(*args, **kwargs)


def gaememcached(config, args, kwargs):
    return memcached(config, args, kwargs)


def saslmemcached(config, args, kwargs):
    args.append(config["CACHE_MEMCACHED_SERVERS"])
    kwargs.update(
        dict(
            username=config["CACHE_MEMCACHED_USERNAME"],
            password=config["CACHE_MEMCACHED_PASSWORD"],
            key_prefix=config["CACHE_KEY_PREFIX"],
        )
    )
    return SASLMemcachedCache(*args, **kwargs)


def spreadsaslmemcached(config, args, kwargs):
    args.append(config["CACHE_MEMCACHED_SERVERS"])
    kwargs.update(
        dict(
            username=config.get("CACHE_MEMCACHED_USERNAME"),
            password=config.get("CACHE_MEMCACHED_PASSWORD"),
            key_prefix=config.get("CACHE_KEY_PREFIX"),
        )
    )

    return SpreadSASLMemcachedCache(*args, **kwargs)
