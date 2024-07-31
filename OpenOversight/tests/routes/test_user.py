from http import HTTPStatus

from flask import current_app

from OpenOversight.app.utils.constants import ENCODING_UTF_8
from OpenOversight.tests.routes.route_helpers import login_user


def test_user_can_see_own_profile(mockdata, client, session):
    with current_app.test_request_context():
        _, user = login_user(client)
        rv = client.get(f"/user/{user.username}")

        assert rv.status_code == HTTPStatus.OK
        assert bytes(f"Profile: {user.username}", ENCODING_UTF_8) in rv.data
