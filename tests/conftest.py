import errno
import pytest

from falcon_caching import Cache

try:
    __import__("pytest_xprocess")
    from xprocess import ProcessStarter
except ImportError:

    @pytest.fixture(scope="session")
    def xprocess():
        pytest.skip("pytest-xprocess not installed.")

# the different cache_types that will be tested
CACHE_TYPES = [
    'simple',
    'filesystem',
    'redis',
    'redissentinel',
    'uwsgi',
    'memcached',
    'gaememcached',
    'saslmemcached',
    'spreadsaslmemcached',
]

# we want to test the pruning, so we set the threshold low
# instead of the default 500
CACHE_THRESHOLD = 5

# which port the Redis server will be listening on
# which is started by xprocess
REDIS_PORT = 63799


# parametrized fixture to create different type caches
@pytest.fixture(params=CACHE_TYPES)
def cache(request, tmp_path, redis_server, memcache_server):
    if request.param == 'redissentinel':
        pytest.skip("We have no Redis Sentinel cluster so we are skipping it")

    # uwsgi tests should only run if running under uwsgi
    if request.param == 'uwsgi':
        try:
            import uwsgi
        except ImportError:
            pytest.skip("uWSGI could not be imported, are you running under uWSGI?")
            return None

    cache = Cache(
        config={
            'CACHE_TYPE': request.param,
            'CACHE_THRESHOLD': CACHE_THRESHOLD,
            'CACHE_DIR': tmp_path if request.param == 'filesystem' else None,
            'CACHE_REDIS_PORT': REDIS_PORT
        }
    )
    return cache.cache


@pytest.fixture(scope="class")
def redis_server(xprocess):
    try:
        import redis
    except ImportError:
        pytest.skip("Python package 'redis' is not installed.")

    class Starter(ProcessStarter):
        pattern = "[Rr]eady to accept connections"
        args = ["redis-server", "--port", REDIS_PORT]

    try:
        xprocess.ensure("redis_server", Starter)
    except IOError as e:
        # xprocess raises FileNotFoundError
        if e.errno == errno.ENOENT:
            pytest.skip("Redis is not installed.")
        else:
            raise

    yield
    xprocess.getinfo("redis_server").terminate()


@pytest.fixture(scope="class")
def memcache_server(xprocess):
    try:
        import pylibmc as memcache
    except ImportError:
        try:
            from google.appengine.api import memcache
        except ImportError:
            try:
                import memcache
            except ImportError:
                pytest.skip(
                    "Python package for memcache is not installed. Need one of "
                    "pylibmc', 'google.appengine', or 'memcache'."
                )

    class Starter(ProcessStarter):
        pattern = ""
        args = ["memcached"]

    try:
        xprocess.ensure("memcached", Starter)
    except IOError as e:
        # xprocess raises FileNotFoundError
        if e.errno == errno.ENOENT:
            pytest.skip("Memcached is not installed.")
        else:
            raise

    yield
    xprocess.getinfo("memcached").terminate()
