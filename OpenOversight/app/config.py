import os


basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    def __init__(self):
        # App Settings
        self.DEBUG = False
        self.SEED = 666
        self.TESTING = False
        # Use session cookie to store URL to redirect to after login
        # https://flask-login.readthedocs.io/en/latest/#customizing-the-login-process
        self.USE_SESSION_FOR_NEXT = True

        # DB Settings
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")

        # Protocol Settings
        self.SITEMAP_URL_SCHEME = "http"

        # Pagination Settings
        self.OFFICERS_PER_PAGE = int(os.environ.get("OFFICERS_PER_PAGE", 20))
        self.USERS_PER_PAGE = int(os.environ.get("USERS_PER_PAGE", 20))

        # Form Settings
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "changemeplzorelsehax")
        self.WTF_CSRF_ENABLED = True

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

        # AWS Settings
        self.AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
        self.AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")
        self.AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")

        # Upload Settings
        self.ALLOWED_EXTENSIONS = set(["jpeg", "jpg", "jpe", "png", "gif", "webp"])
        self.MAX_CONTENT_LENGTH = 50 * 1024 * 1024

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
    "development": DevelopmentConfig(),
    "testing": TestingConfig(),
    "production": ProductionConfig(),
}
config["default"] = config.get(os.environ.get("FLASK_ENV", ""), DevelopmentConfig())
