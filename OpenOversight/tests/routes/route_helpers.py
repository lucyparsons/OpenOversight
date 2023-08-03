from flask import url_for

from OpenOversight.app.auth.forms import LoginForm
from OpenOversight.app.models.database import User
from OpenOversight.app.utils.constants import ADMIN_PASSWORD
from OpenOversight.tests.conftest import AC_DEPT


def login_user(client):
    user = User.query.filter_by(id=1).first()
    form = LoginForm(email=user.email, password="dog", remember_me=True)
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)
    return rv


def login_unconfirmed_user(client):
    user = User.query.filter_by(confirmed=False).first()
    form = LoginForm(email=user.email, password="dog", remember_me=True)
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)
    assert b"Invalid username or password" not in rv.data
    return rv


def login_disabled_user(client):
    form = LoginForm(email="may@example.org", password="yam", remember_me=True)
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=True)
    return rv


def login_modified_disabled_user(client):
    form = LoginForm(email="sam@example.org", password="the yam", remember_me=True)
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=True)
    return rv


def login_admin(client):
    user = User.query.filter_by(is_administrator=True).first()
    form = LoginForm(email=user.email, password=ADMIN_PASSWORD, remember_me=True)
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)
    return rv


def login_ac(client):
    user = User.query.filter_by(ac_department_id=AC_DEPT).first()
    form = LoginForm(email=user.email, password="horse", remember_me=True)
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)
    return rv


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
