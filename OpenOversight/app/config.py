import os


basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    def __init__(self):
        # DB SETUP
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SQLALCHEMY_DATABASE_URI = os.environ.get(
            "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:"
        )

        # Protocol Settings
        self.SITEMAP_URL_SCHEME = "http"

        # pagination
        self.OFFICERS_PER_PAGE = os.environ.get("OFFICERS_PER_PAGE", 20)
        self.USERS_PER_PAGE = os.environ.get("USERS_PER_PAGE", 20)

        # Form Settings
        self.WTF_CSRF_ENABLED = True
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "changemeplzorelsehax")

        # Mail Settings
        self.MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.googlemail.com")
        self.MAIL_PORT = 587
        self.MAIL_USE_TLS = True
        self.MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
        self.MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
        self.OO_MAIL_SUBJECT_PREFIX = os.environ.get(
            "OO_MAIL_SUBJECT_PREFIX", "[OpenOversight]"
        )
        self.OO_MAIL_SENDER = os.environ.get(
            "OO_MAIL_SENDER", "OpenOversight <OpenOversight@gmail.com>"
        )
        # OO_ADMIN = os.environ.get('OO_ADMIN')

        # AWS Settings
        self.AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
        self.AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")
        self.S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")

        # Upload Settings
        self.MAX_CONTENT_LENGTH = 50 * 1024 * 1024
        self.ALLOWED_EXTENSIONS = set(["jpeg", "jpg", "jpe", "png", "gif", "webp"])

        # User settings
        self.APPROVE_REGISTRATIONS = os.environ.get("APPROVE_REGISTRATIONS", False)

        # Use session cookie to store URL to redirect to after login
        # https://flask-login.readthedocs.io/en/latest/#customizing-the-login-process
        self.USE_SESSION_FOR_NEXT = True

        self.SEED = 666

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(BaseConfig):
    def __init__(self):
        super().__init__()
        self.DEBUG = True
        self.SQLALCHEMY_ECHO = True
        self.NUM_OFFICERS = 15000


class TestingConfig(BaseConfig):
    def __init__(self):
        super().__init__()
        self.TESTING = True
        self.WTF_CSRF_ENABLED = False
        self.NUM_OFFICERS = 120
        self.RATELIMIT_ENABLED = False


class ProductionConfig(BaseConfig):
    def __init__(self):
        super().__init__()
        self.SITEMAP_URL_SCHEME = "https"

    @classmethod
    def init_app(cls, app):  # pragma: no cover
        config.init_app(app)


config = {
    "development": DevelopmentConfig(),
    "testing": TestingConfig(),
    "production": ProductionConfig(),
}
config["default"] = config.get(os.environ.get("FLASK_ENV", ""), DevelopmentConfig())
