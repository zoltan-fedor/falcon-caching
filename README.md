[![Build Status](https://travis-ci.com/zoltan-fedor/falcon-caching.svg?branch=master)](https://travis-ci.com/zoltan-fedor/falcon-caching)
[![codecov](https://codecov.io/gh/zoltan-fedor/falcon-caching/branch/master/graph/badge.svg)](https://codecov.io/gh/zoltan-fedor/falcon-caching)
[![Documentation Status](https://readthedocs.org/projects/falcon-caching/badge/?version=latest)](https://falcon-caching.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/zoltan-fedor/falcon-caching)

# Falcon-Caching

This library provides cache support for the [Falcon web framework](https://github.com/falconry/falcon).

It is a port of the popular [Flask-Caching](https://github.com/sh4nks/flask-caching) library.

The library aims to be compatible with CPython 3.6+ and PyPy 3.5+.


## Documentation

You can find the documentation of this library on [Read the Docs](https://falcon-caching.readthedocs.io/en/latest/).


## Quickstart


Quick example:
```
import falcon
from falcon_caching import Cache

# setup the cache instance
cache = Cache(
    config=
    {
        'CACHE_EVICTION_STRATEGY': 'time-based',  # how records are evicted
        'CACHE_TYPE': 'simple'  # what backend to use to store the cache
    })

class ThingsResource:
    # mark the method as cached
    @cache.cached(timeout=600)
    def on_get(self, req, resp):
        pass

# add the cache middleware to the Falcon app
app = falcon.API(middleware=cache.middleware)

things = ThingsResource()

app.add_route('/things', things)
```

Alternatively you could cache the whole resource:
```
# mark the whole resource - all its 'on_' methods as cached
@cache.cached(timeout=600)
class ThingsResource:
    def on_get(self, req, resp):
        pass

    def on_post(self, req, resp):
        pass
```

> **NOTE:**  
> Be careful with the order of middlewares. The `cache.middleware` will
short-circuit any further processing if a cached version of that resource is found.
It will skip any remaining `process_request` and `process_resource` methods,
as well as the `responder` method that the request would have been routed to.
However, any `process_response` middleware methods will still be called.
>
> This is why it is suggested that you add the `cache.middleware` **following** any
authentication / authorization middlewares to avoid unauthorized access of records
served from the cache.

## Development

For the development environment we use `Pipenv` and for packaging we use `Flit`.

### Documentation

The documentation is built via Sphinx following the 
[Google docstring style](https://www.sphinx-doc.org/en/master/usage/extensions/example_google.html#example-google) 
and hosted on [Read the Docs](https://falcon-caching.readthedocs.io/en/latest/).

To review the documentation locally before committing:
```
$ cd docs
$ python -m http.server 8088
```

Now you can access the documentation locally under `http://127.0.0.1:8088/_build/html/`

### Development environment

To be able to test memcached the `pylibmc` library should be installed, which requires
the memcached source to compile, so you will need to install libmemcached-dev first:
```
$ sudo apt-get install libmemcached-dev
```

You will also need Memcached, Redis and Redis Sentinel to be installed 
to be able to test against those locally:
```
$ sudo apt-get install memcached redis-server redis-sentinel
```

You will also need Python 3.6-3.8 and PyPy3 and its source package installed to run
`tox` in all environments.

We do use type hinting and run MyPy on those, but unfortunately MyPy currently breaks
the PyPy tests due to the `typed-ast` package's "bug" (see
https://github.com/python/typed_ast/issues/97). Also with Pipenv you can't 
have a second Pipfile. This is why for now we don't have `mypy` listed as a dev package
in the Pipfile.

## Credits

As this is a port of the popular [Flask-Caching](https://github.com/sh4nks/flask-caching) library
onto the [Falcon web framework](https://github.com/falconry/falcon), parts of the code is copied
from the [Flask-Caching](https://github.com/sh4nks/flask-caching) library.
