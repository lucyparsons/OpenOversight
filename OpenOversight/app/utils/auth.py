from functools import wraps
from http import HTTPStatus

from flask import abort
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous or not current_user.is_administrator:
            abort(HTTPStatus.FORBIDDEN)
        return f(*args, **kwargs)

    return decorated_function


def ac_or_admin_required(f):
    """Decorate that requires that the user be an area coordinator or administrator."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous or not (
            current_user.is_administrator or current_user.is_area_coordinator
        ):
            abort(HTTPStatus.FORBIDDEN)
        return f(*args, **kwargs)

    return decorated_function
