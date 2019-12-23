# Falcon-Caching

Cache support added to the [Falcon web framework](https://github.com/falconry/falcon).

It is a port of the popular [Flask-Caching](https://github.com/sh4nks/flask-caching) library.

The library aims to be compatible with CPython 3.6+ and PyPy 3.5+.


## Documentation

You can find the documentation of this library on [Read the Docs](https://falcon-caching.readthedocs.io/en/latest/).


## Quickstart


Quick example:
```
import falcon
from falcon_caching import Cache

# setup the caching
cache = Cache(config={'CACHE_TYPE': 'simple'})


class ThingsResource:

    # mark the method as cached
    @cache.cached(timeout=600)
    def on_get(self, req, resp):
        pass


# add the cache middleware
app = falcon.API(middleware=cache.middleware)

things = ThingsResource()

app.add_route('/things', things)
```

Alternatively you could cache the whole resource:
```
# mark the whole resource as cached
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

### Documentation

The documentation is built via Sphinx following the 
[Google docstring style](https://www.sphinx-doc.org/en/master/usage/extensions/example_google.html#example-google) 
and hosted on [Read the Docs](https://falcon-caching.readthedocs.io/en/latest/).

To test the documentation locally before committing:
```
$ cd docs
$ python -m http.server 8088
```

Now you can access the documentation locally under `http://127.0.0.1:8088/_build/html/`

### Development environment

To be able to test memcached the `pylibmc` library will be installed, which requires
the memcached source to compile, so you will need to install libmemcached-dev first:
```
$ sudo apt-get install libmemcached-dev
```

You also need Memcached and Redis to be installed to be able to test against those:
```
$ sudo apt-get install memcached redis-server
```

You will also need Pyton 3.6-3.8 and PyPy3 and its source package installed to run
tox in all environments.

Unfortunately MyPy breaks the PyPy tests due to the typed-ast package's "bug":
https://github.com/python/typed_ast/issues/97 and with Pipenv you can't really
have a different Pipfile, so it would try to install it and fail, so for now
we don't have mypy listed as a dev dependency in Pipfile.

## Credits

As this is a port of the popular [Flask-Caching](https://github.com/sh4nks/flask-caching) library
onto the [Falcon web framework](https://github.com/falconry/falcon), parts of the code is copied
from the [Flask-Caching](https://github.com/sh4nks/flask-caching) library.
