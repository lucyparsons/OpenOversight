# Routing and view tests
import pytest
from flask import url_for, current_app
from .route_helpers import login_user, login_admin, login_ac


@pytest.mark.parametrize("route", [
    ('/'),
    ('/index'),
    ('/browse'),
    ('/find'),
    ('/about'),
    ('/privacy'),
    ('/submit'),
    ('/label'),
    ('/tutorial'),
])
def test_routes_ok(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 200


def test_user_can_access_profile(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('main.profile', username='test_user'),
            follow_redirects=True
        )
        assert 'test_user' in rv.data
        # User email should not appear
        assert 'User Email' not in rv.data
        # Toggle button should not appear for this non-admin user
        assert 'Toggle (Disable/Enable) User' not in rv.data


def test_admin_sees_toggle_button_on_profiles(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        rv = client.get(
            url_for('main.profile', username='test_user'),
            follow_redirects=True
        )
        assert 'test_user' in rv.data
        # User email should appear
        assert 'User Email' in rv.data
        # Admin should be able to see the Toggle button
        assert 'Toggle (Disable/Enable) User' in rv.data


def test_admin_can_toggle_user(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        rv = client.post(
            url_for('main.toggle_user', uid=1),
            follow_redirects=True
        )
        assert 'Disabled' in rv.data


def test_ac_cannot_toggle_user(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        rv = client.post(
            url_for('main.toggle_user', uid=1),
            follow_redirects=True
        )
        assert rv.status_code == 403


def test_user_cannot_toggle_user(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.post(
            url_for('main.toggle_user', uid=1),
            follow_redirects=True
        )
        assert rv.status_code == 403
