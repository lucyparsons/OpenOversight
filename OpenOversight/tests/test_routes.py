# Routing and view tests
import pytest
from flask import url_for, current_app
from urlparse import urlparse

from OpenOversight.app.main.forms import (FindOfficerIDForm, FaceTag)
from OpenOversight.app.auth.forms import (LoginForm, RegistrationForm,
                                          ChangePasswordForm, PasswordResetForm,
                                          PasswordResetRequestForm,
                                          ChangeEmailForm)
from OpenOversight.app.models import User, Face


@pytest.mark.parametrize("route", [
    ('/'),
    ('/index'),
    ('/find'),
    ('/about'),
    ('/tagger_find'),
    ('/contact'),
    ('/privacy'),
    ('/label'),
    ('/officer/3'),
    ('/tutorial'),
    ('/auth/login'),
    ('/auth/register'),
    ('/auth/reset'),
    ('/complaint?officer_star=1901&officer_first_name=HUGH&officer_last_name=BUTZ&officer_middle_initial=&officer_image=static%2Fimages%2Ftest_cop2.png')
])
def test_routes_ok(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 200


# All login_required views should redirect if there is no user logged in
@pytest.mark.parametrize("route", [
    ('/submit'),
    ('/auth/unconfirmed'),
    ('/sort'),
    ('/cop_face'),
    ('/image/1'),
    ('/image/tagged/1'),
    ('/tag/1'),
    ('/leaderboard'),
    ('/auth/logout'),
    ('/auth/confirm/abcd1234'),
    ('/auth/confirm'),
    ('/auth/change-password'),
    ('/auth/change-email'),
    ('/auth/change-email/abcd1234')
])
def test_route_login_required(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 302


# POST-only routes
@pytest.mark.parametrize("route", [
    ('/tag/delete/1'),
    ('/image/classify/1/1')
])
def test_route_post_only(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 405


# def test_find_form_submission(client, mockdata):
#     with current_app.test_request_context():
#         form = FindOfficerForm()
#         assert form.validate() == True
#         rv = client.post(url_for('main.get_officer'), data=form.data, follow_redirects=False)
#         assert rv.status_code == 307
#         assert urlparse(rv.location).path == '/gallery'
#
#
# def test_bad_form(client, mockdata):
#     with current_app.test_request_context():
#         form = FindOfficerForm(dept='')
#         assert form.validate() == False
#         rv = client.post(url_for('main.get_officer'), data=form.data, follow_redirects=False)
#         assert rv.status_code == 307
#         assert urlparse(rv.location).path == '/find'
#
#
# def test_find_form_redirect_submission(client, session):
#     with current_app.test_request_context():
#         form = FindOfficerForm()
#         assert form.validate() == True
#         rv = client.post(url_for('main.get_officer'), data=form.data, follow_redirects=False)
#         assert rv.status_code == 200


def test_tagger_lookup(client, session):
    with current_app.test_request_context():
        form = FindOfficerIDForm()
        assert form.validate() is True
        rv = client.post(url_for('main.get_ooid'), data=form.data,
                         follow_redirects=False)
        assert rv.status_code == 307
        assert urlparse(rv.location).path == '/tagger_gallery'


def test_tagger_gallery(client, session):
    with current_app.test_request_context():
        form = FindOfficerIDForm()
        assert form.validate() is True
        rv = client.post(url_for('main.get_tagger_gallery'), data=form.data)
        assert rv.status_code == 200


def test_tagger_gallery_bad_form(client, session):
    with current_app.test_request_context():
        form = FindOfficerIDForm(dept='')
        assert form.validate() is False
        rv = client.post(url_for('main.get_tagger_gallery'), data=form.data,
                         follow_redirects=False)
        assert rv.status_code == 307
        assert urlparse(rv.location).path == '/tagger_find'


def login_user(client):
    form = LoginForm(email='jen@example.org',
                     password='dog',
                     remember_me=True)
    rv = client.post(
        url_for('auth.login'),
        data=form.data,
        follow_redirects=False
    )
    return rv


def login_admin(client):
    form = LoginForm(email='redshiftzero@example.org',
                     password='cat',
                     remember_me=True)
    rv = client.post(
        url_for('auth.login'),
        data=form.data,
        follow_redirects=False
    )
    return rv


def test_valid_user_can_login(mockdata, client, session):
    with current_app.test_request_context():
        rv = login_user(client)
        assert rv.status_code == 302
        assert urlparse(rv.location).path == '/index'


def test_invalid_user_cannot_login(mockdata, client, session):
    with current_app.test_request_context():
        form = LoginForm(email='freddy@example.org',
                         password='bruteforce',
                         remember_me=True)
        rv = client.post(
            url_for('auth.login'),
            data=form.data
        )
        assert 'Invalid username or password.' in rv.data


def test_user_can_logout(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('auth.logout'),
            follow_redirects=True
        )
        assert 'You have been logged out.' in rv.data


def test_logged_in_user_can_access_sort_form(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('main.sort_images'),
            follow_redirects=True
        )
        assert 'Do you see at least one face of a police officer' in rv.data


def test_user_can_access_profile(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('main.profile', username='test_user'),
            follow_redirects=True
        )
        assert 'test_user' in rv.data
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
        # Admin should be able to see the Toggle button
        assert 'Toggle (Disable/Enable) User' in rv.data


def test_user_can_access_officer_profile(mockdata, client, session):
    with current_app.test_request_context():
        rv = client.get(
            url_for('main.officer_profile', officer_id=3),
            follow_redirects=True
        )
        assert 'Officer Detail' in rv.data


def test_user_can_view_submission(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('main.display_submission', image_id=1),
            follow_redirects=True
        )
        assert 'Image ID' in rv.data


def test_user_can_view_tag(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('main.display_tag', tag_id=1),
            follow_redirects=True
        )
        assert 'Tag' in rv.data


def test_admin_can_toggle_user(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        rv = client.post(
            url_for('main.toggle_user', uid=1),
            follow_redirects=True
        )
        assert 'Disabled' in rv.data


def test_admin_can_delete_tag(mockdata, client, session):
    with current_app.test_request_context():
        login_admin(client)

        rv = client.post(
            url_for('main.delete_tag', tag_id=1),
            follow_redirects=True
        )
        assert 'Deleted this tag' in rv.data


def test_user_can_add_tag(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        form = FaceTag(officer_id=1,
                       image_id=4,
                       dataX=34,
                       dataY=32,
                       dataWidth=3,
                       dataHeight=33)

        rv = client.post(
            url_for('main.label_data', image_id=4),
            data=form.data,
            follow_redirects=True
        )
        assert 'Tag added to database' in rv.data


def test_user_cannot_add_tag_if_it_exists(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        tag = Face.query.first()
        form = FaceTag(officer_id=tag.officer_id,
                       image_id=tag.img_id,
                       dataX=34,
                       dataY=32,
                       dataWidth=3,
                       dataHeight=33)

        rv = client.post(
            url_for('main.label_data', image_id=tag.img_id),
            data=form.data,
            follow_redirects=True
        )
        assert 'Tag already exists between this officer and image! Tag not added.' in rv.data


def test_user_can_finish_tagging(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('main.complete_tagging', image_id=4),
            follow_redirects=True
        )
        assert 'Marked image as completed.' in rv.data


def test_user_can_view_leaderboard(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('main.leaderboard'),
            follow_redirects=True
        )
        assert 'Top Users by Number of Images Sorted' in rv.data


def test_user_cannot_register_with_existing_email(mockdata, client, session):
    with current_app.test_request_context():
        form = RegistrationForm(email='jen@example.org',
                                username='redshiftzero',
                                password='dog',
                                password2='dog')
        rv = client.post(
            url_for('auth.register'),
            data=form.data,
            follow_redirects=False
        )

        # Form will return 200 only if the form does not validate
        assert rv.status_code == 200
        assert 'Email already registered' in rv.data


def test_user_cannot_register_if_passwords_dont_match(mockdata, client, session):
    with current_app.test_request_context():
        form = RegistrationForm(email='freddy@example.org',
                                username='b_meson',
                                password='dog',
                                password2='cat')
        rv = client.post(
            url_for('auth.register'),
            data=form.data,
            follow_redirects=False
        )

        # Form will return 200 only if the form does not validate
        assert rv.status_code == 200
        assert 'Passwords must match' in rv.data


def test_user_can_register_with_legit_credentials(mockdata, client, session):
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

        assert 'A confirmation email has been sent to you by email.' in rv.data


def test_user_cannot_register_with_weak_password(mockdata, client, session):
    with current_app.test_request_context():
        form = RegistrationForm(email='jen@example.com',
                                username='redshiftzero',
                                password='weak',
                                password2='weak')
        rv = client.post(
            url_for('auth.register'),
            data=form.data,
            follow_redirects=True
        )

        assert 'A confirmation email has been sent to you by email.' not in rv.data


def test_user_can_get_a_confirmation_token_resent(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)

        rv = client.get(
            url_for('auth.resend_confirmation'),
            follow_redirects=True
        )

        assert 'A new confirmation email has been sent to you by email.' in rv.data


def test_user_can_get_password_reset_token_sent(mockdata, client, session):
    with current_app.test_request_context():
        form = PasswordResetRequestForm(email='jen@example.org')

        rv = client.post(
            url_for('auth.password_reset_request'),
            data=form.data,
            follow_redirects=True
        )

        assert 'An email with instructions to reset your password' in rv.data


def test_user_can_get_reset_password_with_valid_token(mockdata, client, session):
    with current_app.test_request_context():
        form = PasswordResetForm(email='jen@example.org',
                                 password='catdog',
                                 password2='catdog')
        user = User.query.filter_by(email='jen@example.org').one()
        token = user.generate_reset_token()

        rv = client.post(
            url_for('auth.password_reset', token=token),
            data=form.data,
            follow_redirects=True
        )

        assert 'Your password has been updated.' in rv.data


def test_user_cannot_reset_password_with_invalid_token(mockdata, client, session):
    with current_app.test_request_context():
        form = PasswordResetForm(email='jen@example.org',
                                 password='catdog',
                                 password2='catdog')
        token = 'beepboopbeep'

        rv = client.post(
            url_for('auth.password_reset', token=token),
            data=form.data,
            follow_redirects=True
        )

        assert 'Your password has been updated.' not in rv.data


def test_user_cannot_get_email_reset_token_sent_without_valid_password(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        form = ChangeEmailForm(email='jen@example.org',
                               password='dogdogdogdog')

        rv = client.post(
            url_for('auth.change_email_request'),
            data=form.data,
            follow_redirects=True
        )

        assert 'An email with instructions to confirm your new email' not in rv.data


def test_user_can_get_email_reset_token_sent_with_password(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        form = ChangeEmailForm(email='alice@example.org',
                               password='dog')

        rv = client.post(
            url_for('auth.change_email_request'),
            data=form.data,
            follow_redirects=True
        )

        assert 'An email with instructions to confirm your new email' in rv.data


def test_user_can_change_email_with_valid_reset_token(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        user = User.query.filter_by(email='jen@example.org').one()
        token = user.generate_email_change_token('alice@example.org')

        rv = client.get(
            url_for('auth.change_email', token=token),
            follow_redirects=True
        )

        assert 'Your email address has been updated.' in rv.data


def test_user_cannot_change_email_with_invalid_reset_token(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        token = 'beepboopbeep'

        rv = client.get(
            url_for('auth.change_email', token=token),
            follow_redirects=True
        )

        assert 'Your email address has been updated.' not in rv.data


def test_user_can_confirm_account_with_valid_token(mockdata, client, session):
    with current_app.test_request_context():
        login_unconfirmed_user(client)
        user = User.query.filter_by(email='freddy@example.org').one()
        token = user.generate_confirmation_token()

        rv = client.get(
            url_for('auth.confirm', token=token),
            follow_redirects=True
        )

        assert 'You have confirmed your account.' in rv.data


def test_user_can_not_confirm_account_with_invalid_token(mockdata, client,
                                                         session):
    with current_app.test_request_context():
        login_unconfirmed_user(client)
        token = 'beepboopbeep'

        rv = client.get(
            url_for('auth.confirm', token=token),
            follow_redirects=True
        )

        assert 'The confirmation link is invalid or has expired.' in rv.data


def test_user_can_change_password_if_they_match(mockdata, client, session):
    with current_app.test_request_context():
        login_user(client)
        form = ChangePasswordForm(old_password='dog',
                                  password='validpasswd',
                                  password2='validpasswd')

        rv = client.post(
            url_for('auth.change_password'),
            data=form.data,
            follow_redirects=True
        )

        assert 'Your password has been updated.' in rv.data


def login_unconfirmed_user(client):
    form = LoginForm(email='freddy@example.org',
                     password='dog',
                     remember_me=True)
    rv = client.post(
        url_for('auth.login'),
        data=form.data,
        follow_redirects=False
    )
    return rv


def test_unconfirmed_user_redirected_to_confirm_account(mockdata, client,
                                                        session):
    with current_app.test_request_context():
        login_unconfirmed_user(client)

        rv = client.get(
            url_for('auth.unconfirmed'),
            follow_redirects=False
        )

        assert 'Please Confirm Your Account' in rv.data


def test_user_cannot_change_password_if_they_dont_match(mockdata, client,
                                                        session):
    with current_app.test_request_context():
        login_user(client)
        form = ChangePasswordForm(old_password='dog',
                                  password='cat',
                                  password2='butts')

        rv = client.post(
            url_for('auth.change_password'),
            data=form.data,
            follow_redirects=True
        )

        assert 'Passwords must match' in rv.data
