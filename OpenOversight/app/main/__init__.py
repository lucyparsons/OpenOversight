from flask import Blueprint


main = Blueprint("main", __name__)  # noqa

from . import views  # noqa
