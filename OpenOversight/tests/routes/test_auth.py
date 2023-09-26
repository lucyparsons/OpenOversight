from http import HTTPStatus
from unittest import TestCase
from urllib.parse import urlparse

import pytest
from flask import current_app, url_for
from flask_login import current_user

from OpenOversight.app.auth.forms import (
    ChangeDefaultDepartmentForm,
    ChangeEmailForm,
    ChangePasswordForm,
    LoginForm,
    PasswordResetForm,
    PasswordResetRequestForm,
    RegistrationForm,
)
from OpenOversight.app.models.database import User
from OpenOversight.app.utils.constants import KEY_OO_MAIL_SUBJECT_PREFIX
from OpenOversight.tests.conftest import AC_DEPT
from OpenOversight.tests.constants import (
    GENERAL_USER_EMAIL,
    MOD_DISABLED_USER_EMAIL,
    UNCONFIRMED_USER_EMAIL,
)
from OpenOversight.tests.routes.route_helpers import (
    login_disabled_user,
    login_modified_disabled_user,
    login_unconfirmed_user,
    login_user,
)


@pytest.mark.parametrize(
    "route",
    [
        "/auth/login",
        "/auth/register",
        "/auth/reset",
    ],
)
def test_routes_ok(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == HTTPStatus.OK


# All login_required views should redirect if there is no user logged in
@pytest.mark.parametrize(
    "route",
    [
        "/auth/unconfirmed",
        "/auth/logout",
        "/auth/confirm/abcd1234",
        "/auth/confirm",
        "/auth/change-password",
        "/auth/change-email",
        "/auth/change-email/abcd1234",
    ],
)
def test_route_login_required(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == HTTPStatus.FOUND


def test_valid_user_can_login(mockdata, client, session):
    with current_app.test_request_context():
        rv, _ = login_user(client)
        assert rv.status_code == HTTPStatus.FOUND
        assert urlparse(rv.location).path == "/index"


def test_valid_user_can_login_with_email_differently_cased(mockdata, client, session):
    with current_app.test_request_context():
        form = LoginForm(email="JEN@EXAMPLE.ORG", password="dog", remember_me=True)
        rv = client.post(url_for("auth.login"), data=form.data, follow_redirects=False)
        assert rv.status_code == HTTPStatus.FOUND
        assert urlparse(rv.location).path == "/index"


def test_invalid_user_cannot_login(mockdata, client, session):
    with current_app.test_request_context():
        form = LoginForm(
            email=UNCONFIRMED_USER_EMAIL, password="bruteforce", remember_me=True
        )
        rv = client.post(url_for("auth.login"), data=form.data)
        assert b"Invalid username or password." in rv.data


def test_user_can_logout(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(url_for("auth.logout"), follow_redirects=True)
        assert b"You have been logged out." in rv.data


def test_user_cannot_register_with_existing_email(mockdata, client, session):
    with current_app.test_request_context():
        user = User.query.filter_by(is_administrator=True).first()
        form = RegistrationForm(
            email=user.email,
            username=user.username,
            password="dog",
            password2="dog",
        )
        rv = client.post(
            url_for("auth.register"), data=form.data, follow_redirects=False
        )

        # Form will return 200 only if the form does not validate
        assert rv.status_code == HTTPStatus.OK
        assert b"Email already registered" in rv.data


def test_user_cannot_register_with_existing_email_differently_cased(
    mockdata, client, session
):
    with current_app.test_request_context():
        user = User.query.filter_by(is_administrator=True).first()
        form = RegistrationForm(
            email=user.email.upper(),
            username=user.username,
            password="dog",
            password2="dog",
        )
        rv = client.post(
            url_for("auth.register"), data=form.data, follow_redirects=False
        )

        # Form will return 200 only if the form does not validate
        assert rv.status_code == HTTPStatus.OK
        assert b"Email already registered" in rv.data


def test_user_cannot_register_if_passwords_dont_match(mockdata, client, session):
    with current_app.test_request_context():
        user = User.query.filter_by(is_administrator=True).first()
        form = RegistrationForm(
            email=user.email,
            username=user.username,
            password="dog",
            password2="cat",
        )
        rv = client.post(
            url_for("auth.register"), data=form.data, follow_redirects=False
        )

        # Form will return 200 only if the form does not validate
        assert rv.status_code == HTTPStatus.OK
        assert b"Passwords must match" in rv.data


def test_user_can_register_with_legit_credentials(mockdata, client, session, faker):
    with current_app.test_request_context(), TestCase.assertLogs(
        current_app.logger
    ) as log:
        diceware_password = "operative hamster persevere verbalize curling"
        form = RegistrationForm(
            email=faker.ascii_email(),
            username="generic_username",
            password=diceware_password,
            password2=diceware_password,
        )
        rv = client.post(
            url_for("auth.register"), data=form.data, follow_redirects=True
        )

        assert b"A confirmation email has been sent to you." in rv.data
        assert (
            f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} Confirm Your Account"
            in str(log.output)
        )


def test_user_cannot_register_with_weak_password(mockdata, client, session):
    with current_app.test_request_context():
        user = User.query.filter_by(is_administrator=True).first()
        form = RegistrationForm(
            email=user.email,
            username=user.username,
            password="weak",
            password2="weak",
        )
        rv = client.post(
            url_for("auth.register"), data=form.data, follow_redirects=True
        )

        assert b"A confirmation email has been sent to you." not in rv.data


def test_user_can_get_a_confirmation_token_resent(mockdata, client, session):
    with current_app.test_request_context(), TestCase.assertLogs(
        current_app.logger
    ) as log:
        login_user(client)

        rv = client.get(url_for("auth.resend_confirmation"), follow_redirects=True)

        assert b"A new confirmation email has been sent to you." in rv.data
        assert (
            f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} Confirm Your Account"
            in str(log.output)
        )


def test_user_can_get_password_reset_token_sent(mockdata, client, session):
    with current_app.test_request_context(), TestCase.assertLogs(
        current_app.logger
    ) as log:
        user = User.query.filter_by(is_administrator=True).first()
        form = PasswordResetRequestForm(email=user.email)

        rv = client.post(
            url_for("auth.password_reset_request"),
            data=form.data,
            follow_redirects=True,
        )

        assert b"An email with instructions to reset your password" in rv.data
        assert (
            f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} Reset Your Password"
            in str(log.output)
        )


def test_user_can_get_password_reset_token_sent_with_differently_cased_email(
    mockdata, client, session
):
    with current_app.test_request_context(), TestCase.assertLogs(
        current_app.logger
    ) as log:
        user = User.query.filter_by(is_administrator=True).first()
        form = PasswordResetRequestForm(email=user.email.upper())

        rv = client.post(
            url_for("auth.password_reset_request"),
            data=form.data,
            follow_redirects=True,
        )

        assert b"An email with instructions to reset your password" in rv.data
        assert (
            f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} Reset Your Password"
            in str(log.output)
        )


def test_user_can_get_reset_password_with_valid_token(mockdata, client, session):
    with current_app.test_request_context():
        user = User.query.filter_by(is_administrator=True).first()
        form = PasswordResetForm(
            email=user.email, password="catdog", password2="catdog"
        )
        token = user.generate_reset_token()

        rv = client.post(
            url_for("auth.password_reset", token=token),
            data=form.data,
            follow_redirects=True,
        )

        assert b"Your password has been updated." in rv.data


def test_user_can_get_reset_password_with_valid_token_differently_cased(
    mockdata, client, session
):
    with current_app.test_request_context():
        user = User.query.filter_by(is_administrator=True).first()
        form = PasswordResetForm(
            email=user.email.upper(), password="catdog", password2="catdog"
        )
        token = user.generate_reset_token()

        rv = client.post(
            url_for("auth.password_reset", token=token),
            data=form.data,
            follow_redirects=True,
        )

        assert b"Your password has been updated." in rv.data


def test_user_cannot_reset_password_with_invalid_token(mockdata, client, session):
    with current_app.test_request_context():
        user = User.query.filter_by(is_administrator=True).first()
        form = PasswordResetForm(
            email=user.email, password="catdog", password2="catdog"
        )
        token = "beepboopbeep"

        rv = client.post(
            url_for("auth.password_reset", token=token),
            data=form.data,
            follow_redirects=True,
        )

        assert b"Your password has been updated." not in rv.data


def test_user_cannot_reset_password_multiple_times_with_same_token(
    mockdata, client, session
):
    with current_app.test_request_context():
        form = PasswordResetForm(
            email="jen@example.org", password="catdog", password2="catdog"
        )
        user = User.query.filter_by(email="jen@example.org").one()
        token = user.generate_reset_token()

        client.post(
            url_for("auth.password_reset", token=token),
            data=form.data,
            follow_redirects=True,
        )

        rv = client.post(
            url_for("auth.password_reset", token=token),
            data=form.data,
            follow_redirects=True,
        )

        assert b"Your password has been updated." not in rv.data


def test_user_cannot_get_email_reset_token_sent_without_valid_password(
    mockdata, client, session
):
    with current_app.test_request_context():
        login_user(client)
        user = User.query.filter_by(is_administrator=True).first()
        form = ChangeEmailForm(email=user.email, password="dogdogdogdog")

        rv = client.post(
            url_for("auth.change_email_request"), data=form.data, follow_redirects=True
        )

        assert b"An email with instructions to confirm your new email" not in rv.data


def test_user_cannot_get_email_reset_token_sent_to_existing_email(
    mockdata, client, session
):
    with current_app.test_request_context():
        login_user(client)
        user = User.query.filter_by(is_administrator=True).first()
        form = ChangeEmailForm(email=user.email, password="dogdogdogdog")

        rv = client.post(
            url_for("auth.change_email_request"), data=form.data, follow_redirects=True
        )

        assert b"An email with instructions to confirm your new email" not in rv.data


def test_user_cannot_get_email_reset_token_sent_to_existing_email_differently_cased(
    mockdata, client, session
):
    with current_app.test_request_context():
        login_user(client)
        user = User.query.filter_by(is_administrator=True).first()
        form = ChangeEmailForm(email=user.email.upper(), password="dogdogdogdog")

        rv = client.post(
            url_for("auth.change_email_request"), data=form.data, follow_redirects=True
        )

        assert b"An email with instructions to confirm your new email" not in rv.data


def test_user_can_get_email_reset_token_sent_with_password(
    mockdata, client, session, faker
):
    with current_app.test_request_context():
        login_user(client)
        form = ChangeEmailForm(email=faker.ascii_email(), password="dog")

        rv = client.post(
            url_for("auth.change_email_request"), data=form.data, follow_redirects=True
        )

        assert b"An email with instructions to confirm your new email" in rv.data


def test_user_can_change_email_with_valid_reset_token(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        user = User.query.filter_by(is_administrator=False, is_disabled=False).first()
        token = user.generate_email_change_token("alice@example.org")

        rv = client.get(
            url_for("auth.change_email", token=token), follow_redirects=True
        )

        assert b"Your email address has been updated." in rv.data


def test_user_cannot_change_email_with_invalid_reset_token(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        token = "beepboopbeep"

        rv = client.get(
            url_for("auth.change_email", token=token), follow_redirects=True
        )

        assert b"Your email address has been updated." not in rv.data


def test_user_can_confirm_account_with_valid_token(mockdata, client, session):
    with current_app.test_request_context():
        login_unconfirmed_user(client)
        user = User.query.filter_by(confirmed=False).first()
        token = user.generate_confirmation_token()

        rv = client.get(url_for("auth.confirm", token=token), follow_redirects=True)

        assert b"You have confirmed your account." in rv.data


def test_user_can_not_confirm_account_with_invalid_token(mockdata, client, session):
    with current_app.test_request_context():
        login_unconfirmed_user(client)
        token = "beepboopbeep"

        rv = client.get(url_for("auth.confirm", token=token), follow_redirects=True)

        assert b"The confirmation link is invalid or has expired." in rv.data


def test_user_can_change_password_if_they_match(mockdata, client, session):
    with current_app.test_request_context(), TestCase.assertLogs(
        current_app.logger
    ) as log:
        login_user(client)
        form = ChangePasswordForm(
            old_password="dog", password="validpasswd", password2="validpasswd"
        )

        rv = client.post(
            url_for("auth.change_password"), data=form.data, follow_redirects=True
        )

        assert b"Your password has been updated." in rv.data
        assert (
            f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} Your Password Has Changed"
            in str(log.output)
        )


def test_unconfirmed_user_redirected_to_confirm_account(mockdata, client, session):
    with current_app.test_request_context():
        login_unconfirmed_user(client)

        rv = client.get(url_for("auth.unconfirmed"), follow_redirects=False)

        assert b"Please Confirm Your Account" in rv.data


def test_disabled_user_cannot_login(mockdata, client, session):
    with current_app.test_request_context():
        rv, _ = login_disabled_user(client)
        assert b"User has been disabled" in rv.data


def test_disabled_user_cannot_visit_pages_requiring_auth(mockdata, client, session):
    # Don't use modified_disabled_user for anything else! Since we run tests
    # concurrently and this test modifies the user, there's a chance that
    # you'll get unexpected results if both tests run simultaneously.
    with current_app.test_request_context():
        # Temporarily enable account for login
        user = User.query.filter_by(email=MOD_DISABLED_USER_EMAIL).one()
        user.is_disabled = False
        session.add(user)

        rv, _ = login_modified_disabled_user(client)
        assert b"/user/sam" in rv.data

        # Disable account again and check that login_required redirects user correctly
        user.is_disabled = True
        session.add(user)

        # Logged in disabled user cannot access pages requiring auth
        rv = client.get("/auth/logout")
        assert rv.status_code == HTTPStatus.FOUND


def test_user_cannot_change_password_if_they_dont_match(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        form = ChangePasswordForm(old_password="dog", password="cat", password2="butts")

        rv = client.post(
            url_for("auth.change_password"), data=form.data, follow_redirects=True
        )

        assert b"Passwords must match" in rv.data


def test_user_can_change_dept_pref(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        form = ChangeDefaultDepartmentForm(dept_pref=AC_DEPT)

        rv = client.post(
            url_for("auth.change_dept"), data=form.data, follow_redirects=True
        )

        assert b"Updated!" in rv.data

        user = User.query.filter_by(email=GENERAL_USER_EMAIL).one()
        assert user.dept_pref == AC_DEPT


def test_user_email_update_resets_session_token(mockdata, app, session, faker):
    client = current_app.test_client()

    with current_app.app_context(), current_app.test_request_context():
        _, user = login_user(client)
        original_uuid = user.uuid

        # While logged in, user can access leaderboard
        rv = client.get(url_for("main.leaderboard"), follow_redirects=False)
        assert rv.status_code == HTTPStatus.OK

        token = user.generate_email_change_token(faker.ascii_email())
        client.get(url_for("auth.change_email", token=token), follow_redirects=True)
        assert original_uuid != current_user.uuid

    # User is stored in `g` which lasts for the duration of the appcontext,
    # which is typically the lifespan of a request. Splitting this into a
    # separate context so the user will be reloaded properly
    with current_app.app_context(), current_app.test_request_context():
        # When session is invalidated, user is redirected to login page
        rv = client.get(url_for("main.leaderboard"), follow_redirects=False)
        assert rv.status_code == HTTPStatus.FOUND


def test_user_password_update_resets_session_token(mockdata, app, session):
    client = current_app.test_client()

    with current_app.app_context(), current_app.test_request_context():
        _, user = login_user(client)
        original_uuid = user.uuid

        # While logged in, user can access leaderboard
        rv = client.get(url_for("main.leaderboard"), follow_redirects=False)
        assert rv.status_code == HTTPStatus.OK

        # Update user's password
        form = ChangePasswordForm(
            old_password="dog", password="validpasswd", password2="validpasswd"
        )
        client.post(
            url_for("auth.change_password"), data=form.data, follow_redirects=True
        )
        assert original_uuid != current_user.uuid

    with current_app.app_context(), current_app.test_request_context():
        # When session is invalidated, user is redirected to login page
        rv = client.get(url_for("main.leaderboard"), follow_redirects=False)
        assert rv.status_code == HTTPStatus.FOUND
