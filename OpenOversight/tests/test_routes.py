# Routing and view tests
import pytest
from flask import url_for, current_app
from flask_login import current_user
import os
from urlparse import urlparse

from OpenOversight.app.main.forms import (FindOfficerForm, FindOfficerIDForm,
                                          HumintContribution)
from OpenOversight.app.auth.forms import (LoginForm, RegistrationForm,
                                          ChangePasswordForm)
from OpenOversight.app.models import User


@pytest.mark.parametrize("route", [
    ('/'),
    ('/index'),
    ('/find'),
    ('/about'),
    ('/contact'),
    ('/privacy'),
    ('/label'),
    ('/auth/login'),
    ('/auth/register'),
    ('/auth/reset'),
    ('/complaint?officer_star=1901&officer_first_name=HUGH&officer_last_name=BUTZ&officer_middle_initial=&officer_image=static%2Fimages%2Ftest_cop2.png')
])
def test_routes_ok(route, client):
    rv = client.get(route)
    assert rv.status_code == 200


# All login_required views should redirect if there is no user logged in
@pytest.mark.parametrize("route", [
    ('/submit'),
    ('/auth/unconfirmed'),
    ('/auth/logout'),
    ('/auth/confirm/abcd1234'),
    ('/auth/confirm'),
    ('/auth/change-password'),
    ('/auth/change-email'),
    ('/auth/change-email/abcd1234')
])
def test_route_login_required(route, client):
    rv = client.get(route)
    assert rv.status_code == 302

#
# def test_find_form_submission(client, mockdata):
#     with current_app.test_request_context():
#         form = FindOfficerForm()
#         assert form.validate() == True
#         rv = client.post(url_for('main.get_officer'), data=form.data, follow_redirects=False)
#         assert rv.status_code == 307
#         assert urlparse(rv.location).path == '/gallery'
#
#
# def test_bad_form(client, mockdata):
#     with current_app.test_request_context():
#         form = FindOfficerForm(dept='')
#         assert form.validate() == False
#         rv = client.post(url_for('main.get_officer'), data=form.data, follow_redirects=False)
#         assert rv.status_code == 307
#         assert urlparse(rv.location).path == '/find'
#
#
# def test_find_form_redirect_submission(client, session):
#     with current_app.test_request_context():
#         form = FindOfficerForm()
#         assert form.validate() == True
#         rv = client.post(url_for('main.get_officer'), data=form.data, follow_redirects=False)
#         assert rv.status_code == 200


def test_tagger_lookup(client, session):
    with current_app.test_request_context():
        form = FindOfficerIDForm()
        assert form.validate() == True
        rv = client.post(url_for('main.get_ooid'), data=form.data,
                         follow_redirects=False)
        assert rv.status_code == 307
        assert urlparse(rv.location).path == '/tagger_gallery'


def test_tagger_gallery(client, session):
    with current_app.test_request_context():
        form = FindOfficerIDForm()
        assert form.validate() == True
        rv = client.post(url_for('main.get_tagger_gallery'), data=form.data)
        assert rv.status_code == 200


def test_tagger_gallery_bad_form(client, session):
    with current_app.test_request_context():
        form = FindOfficerIDForm(dept='')
        assert form.validate() == False
        rv = client.post(url_for('main.get_tagger_gallery'), data=form.data,
                         follow_redirects=False)
        assert rv.status_code == 307
        assert urlparse(rv.location).path == '/tagger_find'


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


def test_valid_user_can_login(mockdata, client, session):
    with current_app.test_request_context():
        rv = login_user(client)
        assert rv.status_code == 302
        assert urlparse(rv.location).path == '/index'


def test_invalid_user_cannot_login(mockdata, client, session):
    with current_app.test_request_context():
        form = LoginForm(email='freddy@example.org',
                         password='bruteforce',
                         remember_me=True)
        rv = client.post(
            url_for('auth.login'),
            data=form.data
            )
        assert 'Invalid username or password.' in rv.data


def test_user_can_logout(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('auth.logout'),
            follow_redirects=True
            )
        assert 'You have been logged out.' in rv.data


def test_user_cannot_register_with_existing_email(mockdata, client, session):
    with current_app.test_request_context():
        form = RegistrationForm(email='jen@example.org',
                                username='redshiftzero',
                                password='dog',
                                password2='dog')
        rv = client.post(
            url_for('auth.register'),
            data=form.data,
            follow_redirects=False
            )

        # Form will return 200 only if the form does not validate
        assert rv.status_code == 200
        assert 'Email already registered' in rv.data


def test_user_cannot_register_if_passwords_dont_match(mockdata, client, session):
    with current_app.test_request_context():
        form = RegistrationForm(email='freddy@example.org',
                                username='b_meson',
                                password='dog',
                                password2='cat')
        rv = client.post(
            url_for('auth.register'),
            data=form.data,
            follow_redirects=False
            )

        # Form will return 200 only if the form does not validate
        assert rv.status_code == 200
        assert 'Passwords must match' in rv.data


def login_unconfirmed_user(client):
    form = LoginForm(email='freddy@example.org',
                     password='dog',
                     remember_me=True)
    rv = client.post(
        url_for('auth.login'),
        data=form.data,
        follow_redirects=False
        )
    return rv


def test_unconfirmed_user_redirected_to_confirm_account(mockdata, client,
                                                        session):
    with current_app.test_request_context():
        test_user = User(email='freddy@example.org', username='b_meson',
                         password='dog', confirmed=False)
        session.add(test_user)
        session.commit()

        login_unconfirmed_user(client)

        rv = client.get(
            url_for('auth.unconfirmed'),
            follow_redirects=False
            )

        assert 'Please Confirm Your Account' in rv.data


def test_user_cannot_change_password_if_they_dont_match(mockdata, client,
                                                        session):
    with current_app.test_request_context():
        login_user(client)
        form = RegistrationForm(old_password='dog',
                                password='cat',
                                password2='butts')

        rv = client.post(
            url_for('auth.change_password'),
            data=form.data,
            follow_redirects=True
            )

        assert 'Passwords must match' in rv.data


def test_user_cannot_submit_invalid_file_extension(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        with open('tests/test_models.py', "rb") as test_file:
            form = HumintContribution(photo=test_file,
                submit=True)
            rv = client.post(
                url_for('main.submit_data'),
                data=form.data,
                follow_redirects=False
            )
        assert rv.status_code == 200
        assert 'File unable to be uploaded.' in rv.data


def test_user_cannot_submit_malicious_file(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        os.system('touch passwd')
        with open('passwd', "rb") as test_file:
            form = HumintContribution(photo=test_file,
                submit=True)
            rv = client.post(
                url_for('main.submit_data'),
                data=form.data,
                follow_redirects=False
            )
        assert rv.status_code == 200
        assert 'File unable to be uploaded.' in rv.data
