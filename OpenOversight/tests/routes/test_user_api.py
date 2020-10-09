# Routing and view tests
import pytest
from flask import url_for, current_app
from ..conftest import AC_DEPT
from .route_helpers import login_user, login_admin, login_ac


from OpenOversight.app.auth.forms import EditUserForm, RegistrationForm, LoginForm
from OpenOversight.app.models import db, User


routes_methods = [
    ('/auth/users/', ['GET']),
    ('/auth/users/1', ['GET', 'POST']),
    ('/auth/users/1/delete', ['GET', 'POST']),
    ('/auth/users/1/enable', ['GET']),
    ('/auth/users/1/disable', ['GET']),
    ('/auth/users/1/resend', ['GET']),
    ('/auth/users/1/approve', ['GET']),
]


# All login_required views should redirect if there is no user logged in
@pytest.mark.parametrize("route,methods", routes_methods)
def test_user_api_login_required(route, methods, client, mockdata):
    if 'GET' in methods:
        rv = client.get(route)
        assert rv.status_code == 403
    if 'POST' in methods:
        rv = client.post(route)
        assert rv.status_code == 403


@pytest.mark.parametrize("route,methods", routes_methods)
def test_user_cannot_access_user_api(route, methods, mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        if 'GET' in methods:
            rv = client.get(route)
            assert rv.status_code == 403
        if 'POST' in methods:
            rv = client.post(route)
            assert rv.status_code == 403


@pytest.mark.parametrize("route,methods", routes_methods)
def test_ac_cannot_access_user_api(route, methods, mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        if 'GET' in methods:
            rv = client.get(route)
            assert rv.status_code == 403
        if 'POST' in methods:
            rv = client.post(route)
            assert rv.status_code == 403


@pytest.mark.parametrize("route,methods", routes_methods)
def test_admin_can_access_user_api(route, methods, mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        if 'GET' in methods:
            rv = client.get(route)
            assert rv.status_code != 403
        if 'POST' in methods:
            rv = client.post(route)
            assert rv.status_code != 403


def test_admin_can_update_users_to_ac(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.except_(User.query.filter_by(is_administrator=True)).first()
        user_id = user.id

        form = EditUserForm(
            is_area_coordinator=True,
            ac_department=AC_DEPT)

        rv = client.post(
            url_for('auth.user_api', user_id=user_id),
            data=form.data,
            follow_redirects=True
        )

        assert 'updated!' in rv.data.decode('utf-8')
        assert user.is_area_coordinator is True


def test_admin_cannot_update_to_ac_without_department(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.except_(User.query.filter_by(is_administrator=True)).first()
        user_id = user.id

        form = EditUserForm(is_area_coordinator=True)

        rv = client.post(
            url_for('auth.user_api', user_id=user_id),
            data=form.data,
            follow_redirects=True
        )

        assert 'updated!' not in rv.data.decode('utf-8')
        assert user.is_area_coordinator is False


def test_admin_can_update_users_to_admin(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.except_(User.query.filter_by(is_administrator=True)).first()
        user_id = user.id

        form = EditUserForm(
            is_area_coordinator=False,
            is_administrator=True)

        rv = client.post(
            url_for('auth.user_api', user_id=user_id),
            data=form.data,
            follow_redirects=True
        )

        assert 'updated!' in rv.data.decode('utf-8')
        assert user.is_administrator is True


def test_admin_can_delete_user(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.first()
        user_id = user.id
        username = user.username

        rv = client.get(
            url_for('auth.user_api', user_id=user_id) + '/delete',
        )

        assert b'Are you sure you want to delete this user?' in rv.data

        rv = client.post(
            url_for('auth.user_api', user_id=user_id) + '/delete',
            follow_redirects=True
        )

        assert 'User {} has been deleted!'.format(username) in rv.data.decode('utf-8')
        assert not User.query.get(user_id)


def test_admin_can_disable_user(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.first()
        user_id = user.id
        username = user.username

        assert not user.is_disabled

        rv = client.get(
            url_for('auth.user_api', user_id=user_id) + '/disable',
            follow_redirects=True
        )

        assert 'User {} has been disabled!'.format(username) in rv.data.decode('utf-8')

        user = User.query.get(user_id)
        assert user.is_disabled


def test_admin_can_enable_user(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.first()
        user_id = user.id
        username = user.username
        user.is_disabled = True
        db.session.commit()

        user = User.query.get(user_id)
        assert user.is_disabled

        rv = client.get(
            url_for('auth.user_api', user_id=user_id) + '/enable',
            follow_redirects=True
        )

        assert 'User {} has been enabled!'.format(username) in rv.data.decode('utf-8')

        user = User.query.get(user_id)
        assert not user.is_disabled


def test_admin_can_resend_user_confirmation_email(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.filter_by(confirmed=False).first()
        user_id = user.id
        email = user.email

        rv = client.get(
            url_for('auth.user_api', user_id=user_id) + '/resend',
            follow_redirects=True
        )

        assert 'A new confirmation email has been sent to {}.'.format(email) in rv.data.decode('utf-8')


def test_register_user_approval_required(mockdata, client, session):
    current_app.config['APPROVE_REGISTRATIONS'] = True
    with current_app.test_request_context():
        diceware_password = 'operative hamster perservere verbalize curling'
        form = RegistrationForm(email='jen@example.com',
                                username='redshiftzero',
                                password=diceware_password,
                                password2=diceware_password)
        rv = client.post(
            url_for('auth.register'),
            data=form.data,
            follow_redirects=True
        )

        assert 'Once an administrator approves your registration, you will ' \
               'receive a confirmation email to activate your account.' in rv.data.decode('utf-8')

        form = LoginForm(email='jen@example.com',
                         password=diceware_password,
                         remember_me=True)
        rv = client.post(
            url_for('auth.login'),
            data=form.data,
            follow_redirects=False
        )

        assert b'Invalid username or password' not in rv.data

        rv = client.get(
            url_for('auth.unconfirmed'),
            follow_redirects=False
        )

        assert b'administrator has not approved your account yet' in rv.data


def test_admin_can_approve_user(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.first()
        user_id = user.id
        username = user.username
        user.approved = False
        db.session.commit()

        user = User.query.get(user_id)
        assert not user.approved

        rv = client.get(
            url_for('auth.user_api', user_id=user_id) + '/approve',
            follow_redirects=True
        )

        assert 'User {} has been approved!'.format(username) in rv.data.decode('utf-8')

        user = User.query.get(user_id)
        assert user.approved
