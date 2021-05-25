from future.utils import iteritems

from flask import url_for
from OpenOversight.app.auth.forms import LoginForm

ADMIN_EMAIL = "test@example.org"
ADMIN_PASSWORD = "testtest"


def login_user(client):
    form = LoginForm(email='jen@example.org',
                     password='dog',
                     remember_me=True)
    rv = client.post(
        url_for('auth.login'),
        data=form.data,
        follow_redirects=False
    )
    return rv


def login_admin(client):

    form = LoginForm(email=ADMIN_EMAIL,
                     password=ADMIN_PASSWORD,
                     remember_me=True)
    rv = client.post(
        url_for('auth.login'),
        data=form.data,
        follow_redirects=False
    )
    return rv


def login_ac(client):
    form = LoginForm(email='raq929@example.org',
                     password='horse',
                     remember_me=True)
    rv = client.post(
        url_for('auth.login'),
        data=form.data,
        follow_redirects=False
    )
    return rv


def process_form_data(form_dict):
    """Takes the dict from a form with embedded formd and flattens it

        in the way that it is flattened in the browser"""
    new_dict = {}
    for key, value in iteritems(form_dict):

        if type(value) == list:
            if value[0]:
                if type(value[0]) is dict:
                    for idx, item in enumerate(value):
                        for subkey, subvalue in iteritems(item):
                            new_dict['{}-{}-{}'.format(key, idx, subkey)] = subvalue
                elif type(value[0]) is str or type(value[0]) is int:
                    for idx, item in enumerate(value):
                        new_dict['{}-{}'.format(key, idx)] = item
                else:
                    raise ValueError('Lists must contain dicts, strings or ints. {} submitted'.format(type(value[0])))
        elif type(value) == dict:
            for subkey, subvalue in iteritems(value):
                new_dict['{}-{}'.format(key, subkey)] = subvalue
        else:
            new_dict[key] = value

    return new_dict
