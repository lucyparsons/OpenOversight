from cachetools import TTLCache
from cachetools.keys import hashkey

from OpenOversight.app.utils.constants import HOUR


DB_CACHE = TTLCache(maxsize=1024, ttl=12 * HOUR)


def _department_key(department_id: str, update_type: str):
    """Create unique department key."""
    return hashkey(department_id, update_type, "Department")


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
        return _department_key(department.id, update_type)

    return _cache_key


def remove_department_cache_entry(department_id: str, update_type: str):
    """Remove department key from cache if it exists."""

    key = _department_key(department_id, update_type)
    if key in DB_CACHE.keys():
        del DB_CACHE[key]
