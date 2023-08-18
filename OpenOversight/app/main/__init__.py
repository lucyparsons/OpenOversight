from flask import Blueprint


main = Blueprint("main", __name__)

from OpenOversight.app.main import views  # noqa: E402,F401
