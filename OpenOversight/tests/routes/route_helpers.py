from typing import Tuple

from flask import url_for
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from OpenOversight.app.auth.forms import LoginForm
from OpenOversight.app.models.database import User
from OpenOversight.tests.constants import (
    AC_USER_EMAIL,
    AC_USER_PASSWORD,
    ADMIN_USER_EMAIL,
    ADMIN_USER_PASSWORD,
    DISABLED_USER_EMAIL,
    DISABLED_USER_PASSWORD,
    GENERAL_USER_EMAIL,
    GENERAL_USER_PASSWORD,
    MOD_DISABLED_USER_EMAIL,
    MOD_DISABLED_USER_PASSWORD,
    UNCONFIRMED_USER_EMAIL,
    UNCONFIRMED_USER_PASSWORD,
)


def login_user(client: FlaskClient) -> Tuple[TestResponse, User]:
    user = User.query.filter_by(email=GENERAL_USER_EMAIL).first()
    form = LoginForm(email=user.email, password=GENERAL_USER_PASSWORD, remember_me=True)
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)
    return rv, user


def login_unconfirmed_user(client: FlaskClient) -> Tuple[TestResponse, User]:
    user = User.query.filter_by(email=UNCONFIRMED_USER_EMAIL).first()
    form = LoginForm(
        email=user.email, password=UNCONFIRMED_USER_PASSWORD, remember_me=True
    )
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)
    assert b"Invalid username or password" not in rv.data
    return rv, user


def login_disabled_user(client: FlaskClient) -> Tuple[TestResponse, User]:
    user = User.query.filter_by(email=DISABLED_USER_EMAIL).first()
    form = LoginForm(
        email=user.email, password=DISABLED_USER_PASSWORD, remember_me=True
    )
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=True)
    return rv, user


def login_modified_disabled_user(client: FlaskClient) -> Tuple[TestResponse, User]:
    user = User.query.filter_by(email=MOD_DISABLED_USER_EMAIL).first()
    form = LoginForm(
        email=user.email, password=MOD_DISABLED_USER_PASSWORD, remember_me=True
    )
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=True)
    return rv, user


def login_admin(client: FlaskClient) -> Tuple[TestResponse, User]:
    user = User.query.filter_by(email=ADMIN_USER_EMAIL).first()
    form = LoginForm(email=user.email, password=ADMIN_USER_PASSWORD, remember_me=True)
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)
    return rv, user


def login_ac(client: FlaskClient) -> Tuple[TestResponse, User]:
    user = User.query.filter_by(email=AC_USER_EMAIL).first()
    form = LoginForm(email=user.email, password=AC_USER_PASSWORD, remember_me=True)
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)
    return rv, user


def process_form_data(form_dict: dict) -> dict:
    """Mock the browser-flattening of a form containing embedded data."""
    new_dict = {}
    for key, value in form_dict.items():
        if isinstance(value, list):
            if value[0]:
                if isinstance(value[0], dict):
                    for idx, item in enumerate(value):
                        for sub_key, sub_value in item.items():
                            new_dict_key = f"{key}-{idx}-{sub_key}"
                            if not isinstance(sub_value, bool):
                                new_dict[new_dict_key] = sub_value
                            elif sub_value:
                                new_dict[new_dict_key] = "y"
                elif isinstance(value[0], str) or isinstance(value[0], int):
                    for idx, item in enumerate(value):
                        new_dict_key = f"{key}-{idx}"
                        if not isinstance(item, bool):
                            new_dict[new_dict_key] = item
                        elif item:
                            new_dict[new_dict_key] = "y"
                else:
                    raise ValueError(
                        f"Lists must contain dicts, strings or ints. {type(value[0])} submitted"
                    )
        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                new_dict[f"{key}-{sub_key}"] = sub_value
        elif not isinstance(value, bool):
            new_dict[key] = value
        elif value:
            new_dict[key] = "y"

    return new_dict
