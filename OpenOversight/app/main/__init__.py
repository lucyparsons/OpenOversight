from flask import Blueprint


main = Blueprint("main", __name__)

from . import views  # noqa: E402,F401
