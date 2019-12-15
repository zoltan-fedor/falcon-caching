# Falcon-Caching

Cache support added to the [Falcon web framework](https://github.com/falconry/falcon).

This is a port of the popular [Flask-Caching](https://github.com/sh4nks/flask-caching) library

The library aims to be compatible with CPython 3.5+ and PyPy 3.5+.


## Documentation

You can find the documentation of this library on [Read the Docs](https://falcon-caching.readthedocs.io/en/latest/).


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


## Credits

As this is a port of the popular [Flask-Caching](https://github.com/sh4nks/flask-caching) library
onto the [Falcon web framework](https://github.com/falconry/falcon), parts of the code is copied
from the [Flask-Caching](https://github.com/sh4nks/flask-caching) library.
