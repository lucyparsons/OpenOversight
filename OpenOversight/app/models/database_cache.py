from cachetools import TTLCache
from cachetools.keys import hashkey
from flask_sqlalchemy.model import Model

from OpenOversight.app.utils.constants import HOUR


DB_CACHE = TTLCache(maxsize=1024, ttl=12 * HOUR)


def _model_key(model: Model, update_type: str):
    """Create unique db.Model key."""
    return hashkey(model.id, update_type, model.__name__)


def db_model_cache_key(update_type: str):
    """Return a key function to calculate the cache key for db.Model
    methods using the db.Model id and a given update type.

    db.Model.id is used instead of a db.Model obj because the default Python
    __hash__ is unique per obj instance, meaning multiple instances of the same
    department will have different hashes.

    Update type is used in the hash to differentiate between the update types we compute
    per department.
    """

    def _cache_key(model: Model):
        return _model_key(model, update_type)

    return _cache_key


def has_department_cache_entry(department, update_type: str) -> bool:
    """Department key exists in cache."""
    key = _model_key(department, update_type)
    return key in DB_CACHE.keys()


def remove_department_cache_entry(department, update_type: str) -> None:
    """Remove department key from cache if it exists."""
    key = _model_key(department, update_type)
    if key in DB_CACHE.keys():
        del DB_CACHE[key]
