#!/usr/bin/python

from migrate.versioning import api
from migrate.exceptions import DatabaseAlreadyControlledError
from OpenOversight.app import create_app, db, models
app = create_app('development')
db.app = app
import os.path

try:
    db.create_all()

    SQLALCHEMY_MIGRATE_REPO = app.config['SQLALCHEMY_MIGRATE_REPO']
    SQLALCHEMY_DATABASE_URI = app.config['SQLALCHEMY_DATABASE_URI']

    if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
        api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
        api.version_control(SQLALCHEMY_DATABASE_URI,
                           SQLALCHEMY_MIGRATE_REPO)
    else:  # the database already exists
        api.version_control(SQLALCHEMY_DATABASE_URI,
                           SQLALCHEMY_MIGRATE_REPO,
                           api.version(SQLALCHEMY_MIGRATE_REPO))

except DatabaseAlreadyControlledError:
    print "Database already exists, not creating"
