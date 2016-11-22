from migrate.versioning import api # pragma: no cover
import os.path # pragma: no cover

from app import db # pragma: no cover
from config import SQLALCHEMY_DATABASE_URI # pragma: no cover
from config import SQLALCHEMY_MIGRATE_REPO # pragma: no cover

db.create_all() # pragma: no cover

if not os.path.exists(SQLALCHEMY_MIGRATE_REPO): # pragma: no cover
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI,
    	                SQLALCHEMY_MIGRATE_REPO)
else: # pragma: no cover
    # the database already exists
    api.version_control(SQLALCHEMY_DATABASE_URI,
    	                SQLALCHEMY_MIGRATE_REPO,
    	                api.version(SQLALCHEMY_MIGRATE_REPO))