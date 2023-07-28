from flask import url_for

from OpenOversight.app.auth.forms import LoginForm


ADMIN_EMAIL = "test@example.org"
ADMIN_PASSWORD = "testtest"


def login_user(client):
    form = LoginForm(email="jen@example.org", password="dog", remember_me=True)
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)
    return rv


def login_unconfirmed_user(client):
    form = LoginForm(email="freddy@example.org", password="dog", remember_me=True)
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
    form = LoginForm(email=ADMIN_EMAIL, password=ADMIN_PASSWORD, remember_me=True)
    rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)
    return rv


def login_ac(client):
    form = LoginForm(email="raq929@example.org", password="horse", remember_me=True)
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
                        for sub_key, sub_value in item.items():
                            new_dict[f"{key}-{idx}-{sub_key}"] = sub_value
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
            for sub_key, sub_value in value.items():
                new_dict[f"{key}-{sub_key}"] = sub_value
        else:
            new_dict[key] = value

    return new_dict
