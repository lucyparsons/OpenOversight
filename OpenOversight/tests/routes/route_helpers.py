from flask import url_for

from OpenOversight.app.auth.forms import LoginForm
from OpenOversight.app.models.database import User
from OpenOversight.tests.constants import (
    AC_USER_EMAIL,
    AC_USER_PASSWORD,
    ADMIN_USER_EMAIL,
    ADMIN_USER_PASSWORD,
    DISABLED_USER_EMAIL,
    DISABLED_USER_PASSWORD,
    MOD_DISABLED_USER_EMAIL,
    MOD_DISABLED_USER_PASSWORD,
    UNCONFIRMED_USER_EMAIL,
    UNCONFIRMED_USER_PASSWORD,
)


def login_user(client):
    user = User.query.filter_by(id=1).first()
    form = LoginForm(email=user.email, password="dog", remember_me=True)
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)
    return rv, user


def login_unconfirmed_user(client):
    user = User.query.filter_by(email=UNCONFIRMED_USER_EMAIL).first()
    form = LoginForm(
        email=user.email, password=UNCONFIRMED_USER_PASSWORD, remember_me=True
    )
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)
    assert b"Invalid username or password" not in rv.data
    return rv, user


def login_disabled_user(client):
    user = User.query.filter_by(email=DISABLED_USER_EMAIL).first()
    form = LoginForm(
        email=user.email, password=DISABLED_USER_PASSWORD, remember_me=True
    )
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=True)
    return rv, user


def login_modified_disabled_user(client):
    user = User.query.filter_by(email=MOD_DISABLED_USER_EMAIL).first()
    form = LoginForm(
        email=user.email, password=MOD_DISABLED_USER_PASSWORD, remember_me=True
    )
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=True)
    return rv, user


def login_admin(client):
    user = User.query.filter_by(email=ADMIN_USER_EMAIL).first()
    form = LoginForm(email=user.email, password=ADMIN_USER_PASSWORD, remember_me=True)
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)
    return rv, user


def login_ac(client):
    user = User.query.filter_by(email=AC_USER_EMAIL).first()
    form = LoginForm(email=user.email, password=AC_USER_PASSWORD, remember_me=True)
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)
    return rv, user


def process_form_data(form_dict):
    """Mock the browser-flattening of a form containing embedded data."""
    new_dict = {}
    for key, value in form_dict.items():
        if type(value) == list:
            if value[0]:
                if type(value[0]) is dict:
                    for idx, item in enumerate(value):
                        for subkey, subvalue in item.items():
                            new_dict[f"{key}-{idx}-{subkey}"] = subvalue
                elif type(value[0]) is str or type(value[0]) is int:
                    for idx, item in enumerate(value):
                        new_dict[f"{key}-{idx}"] = item
                else:
                    raise ValueError(
                        "Lists must contain dicts, strings or ints. {} submitted".format(
                            type(value[0])
                        )
                    )
        elif type(value) == dict:
            for subkey, subvalue in value.items():
                new_dict[f"{key}-{subkey}"] = subvalue
        else:
            new_dict[key] = value

    return new_dict
