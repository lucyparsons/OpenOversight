from cachetools import TTLCache, cached
from cachetools.keys import hashkey

from OpenOversight.app.utils.constants import HOUR


class CacheClient(object):
    """
    CacheClient is a Singleton class that is used for the TTLCache client.
    This can be fairly easily switched out with another cache type, but it is
    currently defaulted to TTLCache.
    """

    CACHE_DURATION = 12 * HOUR

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = TTLCache(maxsize=1024, ttl=cls.CACHE_DURATION)
        return cls._instance
