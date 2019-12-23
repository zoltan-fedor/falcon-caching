""" The different options available """


class CacheEvictionStrategy:
    """ All implemented cache eviction strategies """
    time_based = 'time-based'
    rest_based = 'rest-based'
    rest_and_time_based = 'rest-and-time-based'


class HttpMethods:
    """ All HTTP methods available """
    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    PUT = 'PUT'
    DELETE = 'DELETE'
