import os


basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    # DB SETUP
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # pagination
    OFFICERS_PER_PAGE = int(os.environ.get("OFFICERS_PER_PAGE", 20))
    USERS_PER_PAGE = int(os.environ.get("USERS_PER_PAGE", 20))

    # Form Settings
    WTF_CSRF_ENABLED = os.environ.get("WTF_CSRF_ENABLED", True)
    SECRET_KEY = os.environ.get("SECRET_KEY", "changemeplzorelsehax")

    # Mail Settings
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.googlemail.com")
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    OO_MAIL_SUBJECT_PREFIX = os.environ.get("OO_MAIL_SUBJECT_PREFIX", "[OpenOversight]")
    OO_MAIL_SENDER = os.environ.get(
        "OO_MAIL_SENDER", "OpenOversight <OpenOversight@gmail.com>"
    )
    # OO_ADMIN = os.environ.get('OO_ADMIN')

    # AWS Settings
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")

    # Upload Settings
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = set(["jpeg", "jpg", "jpe", "png", "gif", "webp"])

    # User settings
    APPROVE_REGISTRATIONS = os.environ.get("APPROVE_REGISTRATIONS", False)

    # Use session cookie to store URL to redirect to after login
    # https://flask-login.readthedocs.io/en/latest/#customizing-the-login-process
    USE_SESSION_FOR_NEXT = True

    SEED = 666

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    NUM_OFFICERS = 15000
    SITEMAP_URL_SCHEME = "http"


class TestingConfig(BaseConfig):
    TESTING = True
    NUM_OFFICERS = 120
    APPROVE_REGISTRATIONS = False
    SITEMAP_URL_SCHEME = "http"
    RATELIMIT_ENABLED = False


class ProductionConfig(BaseConfig):
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
