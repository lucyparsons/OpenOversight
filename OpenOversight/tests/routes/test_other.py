# Routing and view tests
import pytest
from flask import url_for, current_app
from .route_helpers import login_user, login_admin, login_ac, login_inactive_ac

from OpenOversight.app.models import Department
from OpenOversight.app.utils import all_dept_choices
from ..conftest import ACTIVE_NON_AC_DEPT_NAME, INACTIVE_DEPT_NAME, AC_DEPT


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
        assert 'test_user' in rv.data.decode('utf-8')
        # User email should not appear
        assert 'User Email' not in rv.data.decode('utf-8')
        # Toggle button should not appear for this non-admin user
        assert 'Toggle (Disable/Enable) User' not in rv.data.decode('utf-8')


def test_user_profile_shows_to_user_classifications_only_from_active_departments(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('main.profile', username='inactive_ac'),
            follow_redirects=True
        )
        assert INACTIVE_DEPT_NAME not in rv.data.decode('utf-8')
        assert ACTIVE_NON_AC_DEPT_NAME in rv.data.decode('utf-8')


def test_user_profile_shows_to_admin_classifications_from_all_departments(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        rv = client.get(
            url_for('main.profile', username='inactive_ac'),
            follow_redirects=True
        )
        assert INACTIVE_DEPT_NAME in rv.data.decode('utf-8')
        assert ACTIVE_NON_AC_DEPT_NAME in rv.data.decode('utf-8')


def test_user_profile_shows_to_ac_classifications_from_ac_inactive_department(mockdata, client, session):
    with current_app.test_request_context():
        login_inactive_ac(client)

        rv = client.get(
            url_for('main.profile', username='inactive_ac'),
            follow_redirects=True
        )
        assert INACTIVE_DEPT_NAME in rv.data.decode('utf-8')
        assert ACTIVE_NON_AC_DEPT_NAME in rv.data.decode('utf-8')


def test_user_profile_does_not_show_to_ac_classifications_from_non_ac_inactive_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

        rv = client.get(
            url_for('main.profile', username='inactive_ac'),
            follow_redirects=True
        )
        assert INACTIVE_DEPT_NAME not in rv.data.decode('utf-8')
        assert ACTIVE_NON_AC_DEPT_NAME in rv.data.decode('utf-8')


def test_user_profile_shows_to_user_officer_identifications_only_from_active_departments(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        dept = Department.query.filter_by(id=AC_DEPT).one()
        dept.is_active = False

        rv = client.get(
            url_for('main.profile', username='test_ac'),
            follow_redirects=True
        )
        assert dept.name not in rv.data.decode('utf-8')
        assert ACTIVE_NON_AC_DEPT_NAME in rv.data.decode('utf-8')


def test_user_profile_shows_to_admin_officer_identifications_from_all_departments(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        dept = Department.query.filter_by(id=AC_DEPT).one()
        dept.is_active = False

        rv = client.get(
            url_for('main.profile', username='test_ac'),
            follow_redirects=True
        )
        for dept in all_dept_choices():
            assert dept.name in rv.data.decode('utf-8')


def test_user_profile_shows_to_ac_officer_identifications_from_ac_inactive_department(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        dept = Department.query.filter_by(id=AC_DEPT).one()
        dept.is_active = False

        rv = client.get(
            url_for('main.profile', username='test_ac'),
            follow_redirects=True
        )
        assert dept.name in rv.data.decode('utf-8')
        assert ACTIVE_NON_AC_DEPT_NAME in rv.data.decode('utf-8')
        assert INACTIVE_DEPT_NAME not in rv.data.decode('utf-8')


def test_admin_sees_toggle_button_on_profiles(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        rv = client.get(
            url_for('main.profile', username='test_user'),
            follow_redirects=True
        )
        assert 'test_user' in rv.data.decode('utf-8')
        # User email should appear
        assert 'User Email' in rv.data.decode('utf-8')
        # Admin should be able to see the Toggle button
        assert 'Toggle (Disable/Enable) User' in rv.data.decode('utf-8')


def test_admin_can_toggle_user(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        rv = client.post(
            url_for('main.toggle_user', uid=1),
            follow_redirects=True
        )
        assert 'Disabled' in rv.data.decode('utf-8')


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
