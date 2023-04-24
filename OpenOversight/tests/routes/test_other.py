# Routing and view tests
from http import HTTPStatus

import pytest
from flask import current_app, url_for

from OpenOversight.app.utils.constants import ENCODING_UTF_8

from .route_helpers import login_user


@pytest.mark.parametrize(
    "route",
    [
        "/",
        "/index",
        "/browse",
        "/find",
        "/about",
        "/privacy",
        "/submit",
        "/label",
        "/tutorial",
    ],
)
def test_routes_ok(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == HTTPStatus.OK


def test_user_can_access_profile(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for("main.profile", username="test_user"), follow_redirects=True
        )
        assert "test_user" in rv.data.decode(ENCODING_UTF_8)
        # User email should not appear
        assert "User Email" not in rv.data.decode(ENCODING_UTF_8)
        # Toggle button should not appear for this non-admin user
        assert "Edit User" not in rv.data.decode(ENCODING_UTF_8)


def test_user_can_access_profile_differently_cased(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for("main.profile", username="TEST_USER"), follow_redirects=True
        )
        assert "test_user" in rv.data.decode(ENCODING_UTF_8)
        assert "User Email" not in rv.data.decode(ENCODING_UTF_8)
        assert "Edit User" not in rv.data.decode(ENCODING_UTF_8)

        # Should use username in db
        assert "TEST_USER" not in rv.data.decode(ENCODING_UTF_8)
