<<<<<<< HEAD
<<<<<<< HEAD
=======
#!/usr/bin/python

>>>>>>> upstream/develop
=======
>>>>>>> e1e984861d6febe26662280ace18822a855a95ac
from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from app import db
import os.path

db.create_all()

if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI,
    	                SQLALCHEMY_MIGRATE_REPO)
else:  # the database already exists
    api.version_control(SQLALCHEMY_DATABASE_URI,
    	                SQLALCHEMY_MIGRATE_REPO,
<<<<<<< HEAD
<<<<<<< HEAD
    	                api.version(SQLALCHEMY_MIGRATE_REPO))
=======
    	                api.version(SQLALCHEMY_MIGRATE_REPO))
>>>>>>> upstream/develop
=======
    	                api.version(SQLALCHEMY_MIGRATE_REPO))
>>>>>>> e1e984861d6febe26662280ace18822a855a95ac
