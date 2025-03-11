from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_sitemap import Sitemap

from OpenOversight.app.models.users import AnonymousUser


limiter: Limiter = Limiter(
    key_func=get_remote_address, default_limits=["100 per minute", "5 per second"]
)

login_manager: LoginManager = LoginManager()
login_manager.session_protection = "strong"
login_manager.anonymous_user = AnonymousUser
login_manager.login_view = "auth.login"

sitemap: Sitemap = Sitemap()
