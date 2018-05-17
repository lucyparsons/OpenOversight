# Routing and view tests
import pytest
from flask import url_for, current_app
from ..conftest import AC_DEPT
from .route_helpers import login_user, login_admin, login_ac


from OpenOversight.app.auth.forms import EditUserForm
from OpenOversight.app.models import User


# All login_required views should redirect if there is no user logged in
@pytest.mark.parametrize("route", [
    ('/auth/users/'),
    ('/auth/users/1'),
])
def test_route_login_required(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 403


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

        assert 'updated!' in rv.data
        assert user.is_area_coordinator is True


def test_user_cannot_update_users_to_ac(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

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

        assert rv.status_code == 403


def test_ac_cannot_update_users_to_ac(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)

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

        assert rv.status_code == 403


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

        assert 'updated!' not in rv.data
        assert user.is_area_coordinator is False


# def test_admin_can_update_users_to_admin(mockdata, client, session):
#     with current_app.test_request_context():
#         login_admin(client)

#         deparment = Department.query.get(AC_DEPT)
#         user = User.query.except_(User.query.filter_by(is_administrator=True)).first()
#         user_id = user.id

#         form = EditUserForm(
#             is_area_coordinator=False,
#             is_administrator=True)

#         rv = client.post(
#             url_for('auth.user_api', user_id=user_id),
#             data=form.data,
#             follow_redirects=True
#         )

#         assert 'updated!' in rv.data
#         assert user.is_administrator is True
