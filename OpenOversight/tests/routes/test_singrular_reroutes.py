from http import HTTPStatus

from flask import current_app, url_for

from OpenOversight.app.utils.constants import FLASH_MSG_PERMANENT_REDIRECT
from OpenOversight.tests.conftest import AC_DEPT
from OpenOversight.tests.routes.route_helpers import login_admin, login_user


def test_redirect_get_started_labeling(client, session):
    with current_app.test_request_context():
        resp_no_redirect = client.get(
            url_for("main.redirect_get_started_labeling"), follow_redirects=False
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for("main.redirect_get_started_labeling"), follow_redirects=True
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for("main.get_started_labeling")


def test_redirect_sort_images(client, session):
    with current_app.test_request_context():
        login_user(client)
        resp_no_redirect = client.get(
            url_for("main.redirect_sort_images", department_id=AC_DEPT),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for("main.redirect_sort_images", department_id=AC_DEPT),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.sort_images", department_id=AC_DEPT
        )


def test_redirect_officer_profile(client, session):
    with current_app.test_request_context():
        officer_id = 1
        resp_no_redirect = client.get(
            url_for("main.redirect_officer_profile", officer_id=officer_id),
            follow_redirects=False,
        )
        with client.session_transaction() as session:
            flash_message = dict(session["_flashes"]).get("message")

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT
        assert flash_message == FLASH_MSG_PERMANENT_REDIRECT

        resp_redirect = client.get(
            url_for("main.redirect_officer_profile", officer_id=officer_id),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.officer_profile", officer_id=officer_id
        )


def test_redirect_add_assignment(client, session):
    with current_app.test_request_context():
        login_admin(client)
        officer_id = 1
        resp_no_redirect = client.post(
            url_for("main.redirect_add_assignment", officer_id=officer_id),
            follow_redirects=False,
        )

        assert resp_no_redirect.status_code == HTTPStatus.PERMANENT_REDIRECT

        resp_redirect = client.post(
            url_for("main.redirect_add_assignment", officer_id=officer_id),
            follow_redirects=True,
        )
        assert resp_redirect.status_code == HTTPStatus.OK
        assert resp_redirect.request.path == url_for(
            "main.officer_profile", officer_id=officer_id
        )
