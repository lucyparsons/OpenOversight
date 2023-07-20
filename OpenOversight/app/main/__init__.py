from flask import Blueprint

from OpenOversight.app.main import views  # noqa: E402,F401


main = Blueprint("main", __name__)
