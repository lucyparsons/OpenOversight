import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    # DB SETUP
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # pagination
    OFFICERS_PER_PAGE = os.environ.get('OFFICERS_PER_PAGE', 20)
    USERS_PER_PAGE = os.environ.get('USERS_PER_PAGE', 20)

    # Form Settings
    WTF_CSRF_ENABLED = True
    SECRET_KEY = os.environ.get('SECRET_KEY', 'changemeplzorelsehax')

    # Mail Settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    OO_MAIL_SUBJECT_PREFIX = os.environ.get('OO_MAIL_SUBJECT_PREFIX', '[OpenOversight]')
    OO_MAIL_SENDER = os.environ.get('OO_MAIL_SENDER', 'OpenOversight <OpenOversight@gmail.com>')
    # OO_ADMIN = os.environ.get('OO_ADMIN')

    # AWS Settings
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION')
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')

    # Upload Settings
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'jpe', 'png', 'gif'])

    # User settings
    DISABLE_REGISTRATION = os.environ.get('DISABLE_REGISTRATION', False)
    APPROVE_REGISTRATIONS = os.environ.get('APPROVE_REGISTRATIONS', False)

    SEED = 666

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    NUM_OFFICERS = 15000


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    NUM_OFFICERS = 120
    APPROVE_REGISTRATIONS = False


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')

    @classmethod
    def init_app(cls, app):  # pragma: no cover
        config.init_app(app)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
