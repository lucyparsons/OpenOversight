from flask import Blueprint


auth = Blueprint("auth", __name__)

from . import views  # noqa: E402,F401
