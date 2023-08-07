from http import HTTPMethod, HTTPStatus

import pytest
from flask import current_app, url_for

from OpenOversight.app.auth.forms import EditUserForm, LoginForm, RegistrationForm
from OpenOversight.app.models.database import User, db
from OpenOversight.app.utils.constants import ENCODING_UTF_8
from OpenOversight.tests.conftest import AC_DEPT
from OpenOversight.tests.constants import (
    ADMIN_USER_EMAIL,
    GENERAL_USER_EMAIL,
    UNCONFIRMED_USER_EMAIL,
)
from OpenOversight.tests.routes.route_helpers import login_ac, login_admin, login_user


routes_methods = [
    ("/auth/users/", [HTTPMethod.GET]),
    ("/auth/users/1", [HTTPMethod.GET, HTTPMethod.POST]),
    ("/auth/users/1/delete", [HTTPMethod.GET, HTTPMethod.POST]),
]


# All login_required views should redirect if there is no user logged in
@pytest.mark.parametrize("route,methods", routes_methods)
def test_user_api_login_required(route, methods, client, mockdata):
    if HTTPMethod.GET in methods:
        rv = client.get(route)
        assert rv.status_code == HTTPStatus.FORBIDDEN
    if HTTPMethod.POST in methods:
        rv = client.post(route)
        assert rv.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.parametrize("route,methods", routes_methods)
def test_user_cannot_access_user_api(route, methods, mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        if HTTPMethod.GET in methods:
            rv = client.get(route)
            assert rv.status_code == HTTPStatus.FORBIDDEN
        if HTTPMethod.POST in methods:
            rv = client.post(route)
            assert rv.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.parametrize("route,methods", routes_methods)
def test_ac_cannot_access_user_api(route, methods, mockdata, client, session):
    with current_app.test_request_context():
        login_ac(client)
        if HTTPMethod.GET in methods:
            rv = client.get(route)
            assert rv.status_code == HTTPStatus.FORBIDDEN
        if HTTPMethod.POST in methods:
            rv = client.post(route)
            assert rv.status_code == HTTPStatus.FORBIDDEN


def test_admin_can_update_users_to_ac(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.except_(User.query.filter_by(is_administrator=True)).first()

        form = EditUserForm(
            is_area_coordinator=True, ac_department=AC_DEPT, submit=True
        )

        rv = client.post(
            url_for("auth.edit_user", user_id=user.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "updated!" in rv.data.decode(ENCODING_UTF_8)
        assert user.is_area_coordinator is True


def test_admin_cannot_update_to_ac_without_department(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.except_(User.query.filter_by(email=ADMIN_USER_EMAIL)).first()

        form = EditUserForm(is_area_coordinator=True, submit=True)

        rv = client.post(
            url_for("auth.edit_user", user_id=user.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "updated!" not in rv.data.decode(ENCODING_UTF_8)
        assert user.is_area_coordinator is False


def test_admin_can_update_users_to_admin(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.except_(User.query.filter_by(email=ADMIN_USER_EMAIL)).first()

        form = EditUserForm(
            is_area_coordinator=False, is_administrator=True, submit=True
        )

        rv = client.post(
            url_for("auth.edit_user", user_id=user.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "updated!" in rv.data.decode(ENCODING_UTF_8)
        assert user.is_administrator is True


def test_admin_can_delete_user(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.filter_by(email=GENERAL_USER_EMAIL).one()

        rv = client.get(
            url_for("auth.delete_user", user_id=user.id),
        )

        assert b"Are you sure you want to delete this user?" in rv.data

        rv = client.post(
            url_for("auth.delete_user", user_id=user.id), follow_redirects=True
        )

        assert f"User {user.username} has been deleted!" in rv.data.decode(
            ENCODING_UTF_8
        )
        assert not User.query.get(user.id)


def test_admin_cannot_delete_other_admin(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User(is_administrator=True, email="another_user@example.org")
        session.add(user)
        session.commit()

        rv = client.post(
            url_for("auth.delete_user", user_id=user.id), follow_redirects=True
        )

        assert rv.status_code == HTTPStatus.FORBIDDEN
        assert User.query.get(user.id) is not None


def test_admin_can_disable_user(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        # just need to make sure to not select the admin user
        user = User.query.filter_by(is_administrator=False).first()

        assert not user.is_disabled

        form = EditUserForm(
            is_disabled=True,
            submit=True,
        )

        rv = client.post(
            url_for("auth.edit_user", user_id=user.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "updated!" in rv.data.decode(ENCODING_UTF_8)

        user = User.query.get(user.id)
        assert user.is_disabled


def test_admin_cannot_disable_self(mockdata, client, session):
    with current_app.test_request_context():
        _, user = login_admin(client)

        assert not user.is_disabled

        form = EditUserForm(
            is_disabled=True,
            submit=True,
        )

        rv = client.post(
            url_for("auth.edit_user", user_id=user.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "You cannot edit your own account!" in rv.data.decode(ENCODING_UTF_8)

        user = User.query.get(user.id)
        assert not user.is_disabled


def test_admin_can_enable_user(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.filter_by(email=GENERAL_USER_EMAIL).one()
        user.is_disabled = True
        db.session.commit()

        user = User.query.get(user.id)
        assert user.is_disabled

        form = EditUserForm(
            is_disabled=False,
            submit=True,
        )

        rv = client.post(
            url_for("auth.edit_user", user_id=user.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "updated!" in rv.data.decode(ENCODING_UTF_8)

        user = User.query.get(user.id)
        assert not user.is_disabled


def test_admin_can_resend_user_confirmation_email(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.filter_by(email=UNCONFIRMED_USER_EMAIL).first()

        form = EditUserForm(
            resend=True,
        )

        rv = client.post(
            url_for("auth.edit_user", user_id=user.id),
            data=form.data,
            follow_redirects=True,
        )

        assert (
            f"A new confirmation email has been sent to {user.email}."
            in rv.data.decode(ENCODING_UTF_8)
        )


def test_register_user_approval_required(mockdata, client, session):
    current_app.config["APPROVE_REGISTRATIONS"] = True
    with current_app.test_request_context():
        diceware_password = "operative hamster persevere verbalize curling"
        new_user_email = "jen@example.com"
        form = RegistrationForm(
            email=new_user_email,
            username="redshiftzero",
            password=diceware_password,
            password2=diceware_password,
        )
        rv = client.post(
            url_for("auth.register"), data=form.data, follow_redirects=True
        )

        assert (
            "Once an administrator approves your registration, you will "
            "receive a confirmation email to activate your account."
            in rv.data.decode(ENCODING_UTF_8)
        )

        form = LoginForm(
            email=new_user_email, password=diceware_password, remember_me=True
        )
        rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)

        assert b"Invalid username or password" not in rv.data

        rv = client.get(url_for("auth.unconfirmed"), follow_redirects=False)

        assert b"administrator has not approved your account yet" in rv.data


def test_admin_can_approve_user(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.filter_by(email=GENERAL_USER_EMAIL).first()
        user.approved = False
        db.session.commit()

        user = User.query.get(user.id)
        assert not user.approved

        form = EditUserForm(
            approved=True,
            submit=True,
        )

        rv = client.post(
            url_for("auth.edit_user", user_id=user.id),
            data=form.data,
            follow_redirects=True,
        )

        assert "updated!" in rv.data.decode(ENCODING_UTF_8)

        user = User.query.get(user.id)
        assert user.approved


@pytest.mark.parametrize(
    "currently_approved, currently_confirmed, approve_registration_config, "
    "should_send_email",
    [
        # Approving unconfirmed user sends email
        (False, False, True, True),
        # Approving unconfirmed user does not send email if approve_registration
        # config is not set
        (False, False, False, False),
        # Updating approved user does not send email
        (True, False, True, False),
        # Approving confirmed user does not send email
        (False, True, True, False),
    ],
)
def test_admin_approval_sends_confirmation_email(
    currently_approved,
    currently_confirmed,
    should_send_email,
    approve_registration_config,
    mockdata,
    client,
    session,
):
    current_app.config["APPROVE_REGISTRATIONS"] = approve_registration_config
    with current_app.test_request_context():
        login_admin(client)

        user = User.query.filter_by(is_administrator=False).first()
        user.approved = currently_approved
        user.confirmed = currently_confirmed
        db.session.commit()

        user = User.query.get(user.id)
        assert user.approved == currently_approved
        assert user.confirmed == currently_confirmed

        form = EditUserForm(approved=True, submit=True, confirmed=currently_confirmed)

        rv = client.post(
            url_for("auth.edit_user", user_id=user.id),
            data=form.data,
            follow_redirects=True,
        )

        assert (
            "new confirmation email" in rv.data.decode(ENCODING_UTF_8)
        ) == should_send_email
        assert "updated!" in rv.data.decode(ENCODING_UTF_8)

        user = User.query.get(user.id)
        assert user.approved
