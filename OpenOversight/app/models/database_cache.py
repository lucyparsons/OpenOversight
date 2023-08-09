from typing import Any

from cachetools import TTLCache
from cachetools.keys import hashkey
from flask_sqlalchemy.model import Model

from OpenOversight.app.utils.constants import HOUR


DB_CACHE = TTLCache(maxsize=1024, ttl=24 * HOUR)


def model_key(model: Model, update_type: str):
    """Create unique db.Model key."""
    return hashkey(model.id, update_type, model.__class__.__name__)


def model_cache_key(update_type: str):
    """Return a key function to calculate the cache key for db.Model
    methods using the db.Model id and a given update type.

    db.Model.id is used instead of a db.Model obj because the default Python
    __hash__ is unique per obj instance, meaning multiple instances of the same
    department will have different hashes.

    Update type is used in the hash to differentiate between the update types we compute
    per department.
    """

    def _cache_key(model: Model):
        return model_key(model, update_type)

    return _cache_key


def get_cache_entry(model: Model, update_type: str) -> Any:
    """Get db.Model entry for key in the cache."""
    key = model_key(model, update_type)
    if key in DB_CACHE.keys():
        return DB_CACHE.get(key)
    else:
        return None


def has_cache_entry(model: Model, update_type: str) -> bool:
    """db.Model key exists in cache."""
    key = model_key(model, update_type)
    return key in DB_CACHE.keys()


def put_cache_entry(model: Model, update_type: str, data: Any) -> None:
    """Put data in cache using the constructed key."""
    key = model_key(model, update_type)
    DB_CACHE[key] = data


def remove_cache_entry(model: Model, update_type: [str]) -> None:
    """Remove db.Model key from cache if it exists."""
    for ut in update_type:
        key = model_key(model, ut)
        if key in DB_CACHE.keys():
            del DB_CACHE[key]
