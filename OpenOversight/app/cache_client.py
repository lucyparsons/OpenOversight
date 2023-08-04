from cachetools import TTLCache
from cachetools.keys import hashkey

from OpenOversight.app.utils.constants import HOUR


DB_CACHE = TTLCache(maxsize=1024, ttl=12 * HOUR)


def department_statistics_cache_key(update_type: str):
    """Return a key function to calculate the cache key for Department
    methods using the department id and a given update type.

    Department.id is used instead of a Department obj because the default Python
    __hash__ is unique per obj instance, meaning multiple instances of the same
    department will have different hashes.

    Update type is used in the hash to differentiate between the update types we compute
    per department.
    """

    def _cache_key(department):
        return hashkey(department.id, update_type)

    return _cache_key
