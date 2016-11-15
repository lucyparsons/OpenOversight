import os
from os.path import expanduser
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    # DB SETUP
    SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File Upload Settings
    UNLABELLED_UPLOADS = 'uploads/'
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'mpeg', 'mp4'])

    # pagination
    OFFICERS_PER_PAGE = os.environ.get('OFFICERS_PER_PAGE', 20)

    # Form Settings
    WTF_CSRF_ENABLED = True
    SECRET_KEY = 'changemeplzorelsehax'

    NUM_OFFICERS = 120
    SEED = 666

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
