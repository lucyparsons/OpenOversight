from flask import url_for
from OpenOversight.app.auth.forms import LoginForm


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
    form = LoginForm(email='redshiftzero@example.org',
                     password='cat',
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
