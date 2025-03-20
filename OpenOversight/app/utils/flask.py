from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sitemap import Sitemap


limiter: Limiter = Limiter(
    key_func=get_remote_address, default_limits=["100 per minute", "5 per second"]
)

sitemap = Sitemap()
