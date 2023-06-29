import os


basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    # DB Settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Pagination Settings
    OFFICERS_PER_PAGE = os.environ.get("OFFICERS_PER_PAGE", 20)
    USERS_PER_PAGE = os.environ.get("USERS_PER_PAGE", 20)

    # Form Settings
    WTF_CSRF_ENABLED = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "changemeplzorelsehax")

    # Mail Settings
    OO_MAIL_SUBJECT_PREFIX = os.environ.get("OO_MAIL_SUBJECT_PREFIX", "[OpenOversight]")
    OO_SERVICE_EMAIL = os.environ.get("OO_SERVICE_EMAIL")

    # AWS Settings
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")

    # Upload Settings
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = set(["jpeg", "jpg", "jpe", "png", "gif", "webp"])

    # User Settings
    APPROVE_REGISTRATIONS = os.environ.get("APPROVE_REGISTRATIONS", False)

    # Use session cookie to store URL to redirect to after login
    # https://flask-login.readthedocs.io/en/latest/#customizing-the-login-process
    USE_SESSION_FOR_NEXT = True

    # Misc. Settings
    SEED = 666

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    NUM_OFFICERS = 15000
    SITEMAP_URL_SCHEME = "http"


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    NUM_OFFICERS = 120
    APPROVE_REGISTRATIONS = False
    SITEMAP_URL_SCHEME = "http"
    RATELIMIT_ENABLED = False


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    SITEMAP_URL_SCHEME = "https"

    @classmethod
    def init_app(cls, app):  # pragma: no cover
        config.init_app(app)


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
config["default"] = config.get(os.environ.get("FLASK_ENV", ""), DevelopmentConfig)
