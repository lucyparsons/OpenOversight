import os
from os.path import expanduser
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

basedir = os.path.abspath(os.path.dirname(__file__))

# DB SETUP
SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# File Upload Settings
UNLABELLED_UPLOADS = 'uploads/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'mpeg', 'mp4'])

# Form Settings
WTF_CSRF_ENABLED = True
SECRET_KEY = 'changemeplzorelsehax'
