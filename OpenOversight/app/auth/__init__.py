from flask import Blueprint

auth = Blueprint('auth', __name__)  # noqa

from . import views  # noqa
