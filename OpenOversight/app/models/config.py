import os

from OpenOversight.app.utils.constants import (
    KEY_DATABASE_URI,
    KEY_ENV,
    KEY_ENV_DEV,
    KEY_ENV_PROD,
    KEY_ENV_TESTING,
    KEY_OFFICERS_PER_PAGE,
    KEY_OO_MAIL_SUBJECT_PREFIX,
    KEY_S3_BUCKET_NAME,
    KEY_TIMEZONE,
    MEGABYTE,
)


basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    def __init__(self):
        # App Settings
        self.DEBUG = False
        self.ENV = os.environ.get(KEY_ENV, KEY_ENV_DEV)
        self.SEED = 666
        self.TIMEZONE = os.environ.get(KEY_TIMEZONE, "America/Chicago")
        self.TESTING = False
        # Use session cookie to store URL to redirect to after login
        # https://flask-login.readthedocs.io/en/latest/#customizing-the-login-process
        self.USE_SESSION_FOR_NEXT = True

        # DB Settings
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SQLALCHEMY_DATABASE_URI = os.environ.get(KEY_DATABASE_URI)

        # Protocol Settings
        self.SITEMAP_URL_SCHEME = "http"

        # Pagination Settings
        self.OFFICERS_PER_PAGE = int(os.environ.get(KEY_OFFICERS_PER_PAGE, 20))
        self.USERS_PER_PAGE = int(os.environ.get("USERS_PER_PAGE", 20))

        # Form Settings
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "changemeplzorelsehax")
        self.WTF_CSRF_ENABLED = True

        # Mail Settings
        self.OO_MAIL_SUBJECT_PREFIX = os.environ.get(
            KEY_OO_MAIL_SUBJECT_PREFIX, "[OpenOversight]"
        )
        self.OO_SERVICE_EMAIL = os.environ.get("OO_SERVICE_EMAIL")
        # TODO: Remove the default once we are able to update the production .env file
        # TODO: Once that is done, we can re-alpha sort these variables.
        self.OO_HELP_EMAIL = os.environ.get("OO_HELP_EMAIL", self.OO_SERVICE_EMAIL)

        # AWS Settings
        self.AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
        self.AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")
        self.AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.S3_BUCKET_NAME = os.environ.get(KEY_S3_BUCKET_NAME)

        # Upload Settings
        self.ALLOWED_EXTENSIONS = set(["jpeg", "jpg", "jpe", "png", "gif", "webp"])
        self.MAX_CONTENT_LENGTH = 50 * MEGABYTE

        # User settings
        self.APPROVE_REGISTRATIONS = os.environ.get("APPROVE_REGISTRATIONS", False)


class DevelopmentConfig(BaseConfig):
    def __init__(self):
        super(DevelopmentConfig, self).__init__()
        self.DEBUG = True
        self.SQLALCHEMY_ECHO = True
        self.NUM_OFFICERS = 15000


class TestingConfig(BaseConfig):
    def __init__(self):
        super(TestingConfig, self).__init__()
        self.TESTING = True
        self.WTF_CSRF_ENABLED = False
        self.NUM_OFFICERS = 120
        self.RATELIMIT_ENABLED = False
        self.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    def __init__(self):
        super(ProductionConfig, self).__init__()
        self.SITEMAP_URL_SCHEME = "https"


config = {
    KEY_ENV_DEV: DevelopmentConfig(),
    KEY_ENV_TESTING: TestingConfig(),
    KEY_ENV_PROD: ProductionConfig(),
}
config["default"] = config.get(os.environ.get(KEY_ENV, ""), DevelopmentConfig())
