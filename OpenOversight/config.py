import os
from os.path import expanduser

basedir = os.path.abspath(os.path.dirname(__file__))

with open(expanduser(os.environ['PGPASS']), 'r') as f:
    host, port, database, user, password = f.read().rstrip('\n').split(':')

# DB SETUP
SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}/{}'.format(user, password, host, database)
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = True

# File Upload Settings
UNLABELLED_UPLOADS = 'uploads/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'mpeg', 'mp4'])

# pagination
OFFICERS_PER_PAGE = os.environ.get('OFFICERS_PER_PAGE', 20)

# Form Settings
WTF_CSRF_ENABLED = True
SECRET_KEY = 'changemeplzorelsehax'
