from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


limiter: Limiter = Limiter(
    key_func=get_remote_address, default_limits=["100 per minute", "5 per second"]
)
