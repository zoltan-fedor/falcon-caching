

def register(*decorators):
    """ This allows us to register multiple decorators and later being able to
    determine which decorators were registered on the given method

    This is necessary, because our decorators from Middlewares are just marking the method,
    so when the Middleware's process_request() method is called it can determine if the given
    endpoint is decorated, so it needs to take action. If there are multiple decorators,
    then it could only tell the topmost.
    Of you register the decorators with this register() method, then it will be able to tell
    that the method is decorated even if the given decorator is NOT the topmost.

    See https://stackoverflow.com/questions/3232024/introspection-to-get-decorator-names-on-a-method

    Use it as:
        class Foo(object):
            @register(many,decos,here)
            def bar(self):
                pass

        # print just the names of the decorators:
        print([d.func_name for d in foo.bar._decorators])
        >> ['many', 'decos', 'here']
    """
    def register_wrapper(func):
        for deco in decorators[::-1]:
            func = deco(func)
        func._decorators = decorators
        return func
    return register_wrapper
