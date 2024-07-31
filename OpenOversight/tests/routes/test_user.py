from http import HTTPStatus

from flask import current_app

from OpenOversight.app.models.database import User
from OpenOversight.app.utils.constants import ENCODING_UTF_8
from OpenOversight.tests.constants import AC_USER_EMAIL, GENERAL_USER_EMAIL
from OpenOversight.tests.routes.route_helpers import login_ac, login_user, login_admin


def test_user_cannot_see_profile_if_not_logged_in(mockdata, client, session):
    with current_app.test_request_context():
        user = User.query.filter_by(email=GENERAL_USER_EMAIL).first()
        rv = client.get(f"/user/{user.username}")

        # Assert that there is a redirect
        assert rv.status_code == HTTPStatus.FOUND


def test_user_profile_for_invalid_regex_username(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        rv = client.get("/user/this_name_is_mad]]bogus")

        # Assert page returns error
        assert rv.status_code == HTTPStatus.NOT_FOUND


def test_user_profile_for_invalid_username(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        rv = client.get("/user/this_name_is_mad_bogus")

        # Assert page returns error
        assert rv.status_code == HTTPStatus.NOT_FOUND


def test_user_can_see_own_profile(mockdata, client, session):
    with current_app.test_request_context():
        _, user = login_user(client)
        rv = client.get(f"/user/{user.username}")

        assert rv.status_code == HTTPStatus.OK
        assert bytes(f"Profile: {user.username}", ENCODING_UTF_8) in rv.data


def test_user_cannot_see_other_users_profile(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        other_user = User.query.filter_by(email=AC_USER_EMAIL).first()
        rv = client.get(f"/user/{other_user.username}")

        # Assert page returns error
        assert rv.status_code == HTTPStatus.FORBIDDEN


def test_ac_user_cannot_see_other_users_profile(mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        other_user = User.query.filter_by(email=GENERAL_USER_EMAIL).first()
        rv = client.get(f"/user/{other_user.username}")

        # Assert page returns error
        assert rv.status_code == HTTPStatus.FORBIDDEN

def test_admin_user_cannot_see_other_users_profile(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)
        other_user = User.query.filter_by(email=GENERAL_USER_EMAIL).first()
        rv = client.get(f"/user/{other_user.username}")

        # Assert page returns error
        assert rv.status_code == HTTPStatus.FORBIDDEN
