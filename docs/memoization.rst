

Memoization
-----------

.. versionadded:: 0.3

See :py:meth:`.Cache.memoize`

Using the @memoize decorator you are able to cache the result of other non-view related functions.
In memoization, the functions arguments are also included into the cache_key.

.. note::
    Credits must be given to the authors and maintainers of the
    `Flask-Caching <https://github.com/sh4nks/flask-caching>`_ library,
    as much of the code of our memoize method was ported from
    their popular library.

Outside just simple function, memoize is also designed for methods, since it will take into account
the `identity <http://docs.python.org/library/functions.html#id>`_. of the
'self' or 'cls' argument as part of the cache key.

The theory behind memoization is that if you have a function you need
to call several times in one request, it would only be calculated the first
time that function is called with those arguments. For example, an sqlalchemy
object that determines if a user has a role. You might need to call this
function many times during a single request. To keep from hitting the database
every time this information is needed you might do something like the following::

    class Person(db.Model):
        @cache.memoize(50)
        def has_membership(self, role_id):
            return Group.query.filter_by(user=self, role_id=role_id).count() >= 1


.. warning::

    Using mutable objects (classes, etc) as part of the cache key can become
    tricky. It is suggested to not pass in an object instance into a memoized
    function. However, the memoize does perform a repr() on the passed in arguments
    so that if the object has a __repr__ function that returns a uniquely
    identifying string for that object, that will be used as part of the
    cache key.

    For example, an sqlalchemy person object that returns the database id as
    part of the unique identifier::

        class Person(db.Model):
            def __repr__(self):
                return "%s(%s)" % (self.__class__.__name__, self.id)



Deleting memoize cache
**********************

See :py:meth:`.Cache.delete_memoized`

.. versionadded:: 0.3

You might need to delete the cache on a per-function bases. Using the above
example, lets say you change the users permissions and assign them to a role,
but now you need to re-calculate if they have certain memberships or not.
You can do this with the :meth:`~Cache.delete_memoized` function::

    cache.delete_memoized(user_has_membership)

.. note::

  If only the function name is given as parameter, all the memoized versions
  of it will be invalidated. However, you can delete specific cache by
  providing the same parameter values as when caching. In following
  example only the ``user``-role cache is deleted:

  .. code-block:: python

     user_has_membership('demo', 'admin')
     user_has_membership('demo', 'user')

     cache.delete_memoized(user_has_membership, 'demo', 'user')
