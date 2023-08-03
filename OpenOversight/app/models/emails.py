from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app, render_template

from OpenOversight.app.utils.constants import (
    FILE_TYPE_HTML,
    FILE_TYPE_PLAIN,
    KEY_OO_HELP_EMAIL,
    KEY_OO_MAIL_SUBJECT_PREFIX,
    KEY_OO_SERVICE_EMAIL,
)


class Email:
    """Base class for all emails."""

    EMAIL_PATH = "auth/email/"

    def __init__(self, body: str, html: str, subject: str, receiver: str):
        self.body = body
        self.html = html
        self.receiver = receiver
        self.subject = subject

    def create_message(self):
        message = MIMEMultipart("alternative")
        message["To"] = self.receiver
        message["From"] = current_app.config[KEY_OO_SERVICE_EMAIL]
        message["Subject"] = self.subject
        message["Reply-To"] = current_app.config[KEY_OO_HELP_EMAIL]

        message.attach(MIMEText(self.body, FILE_TYPE_PLAIN))
        message.attach(MIMEText(self.html, FILE_TYPE_HTML))

        return message


class AdministratorApprovalEmail(Email):
    def __init__(self, receiver: str, user, admin):
        subject = (
            f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} New User Registered"
        )
        body = render_template(
            f"{self.EMAIL_PATH}new_registration.txt", user=user, admin=admin
        )
        html = render_template(
            f"{self.EMAIL_PATH}new_registration.html", user=user, admin=admin
        )
        super().__init__(body, html, subject, receiver)


class ChangeEmailAddressEmail(Email):
    def __init__(self, receiver: str, user, token: str):
        subject = (
            f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} Confirm Your Email "
            f"Address"
        )
        body = render_template(
            f"{self.EMAIL_PATH}change_email.txt", user=user, token=token
        )
        html = render_template(
            f"{self.EMAIL_PATH}change_email.html", user=user, token=token
        )
        super().__init__(body, html, subject, receiver)


class ChangePasswordEmail(Email):
    def __init__(self, receiver: str, user):
        subject = f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} Your Password Has Changed"
        body = render_template(
            f"{self.EMAIL_PATH}change_password.txt",
            user=user,
            help_email=current_app.config[KEY_OO_HELP_EMAIL],
        )
        html = render_template(
            f"{self.EMAIL_PATH}change_password.html",
            user=user,
            help_email=current_app.config[KEY_OO_HELP_EMAIL],
        )
        super().__init__(body, html, subject, receiver)


class ConfirmAccountEmail(Email):
    def __init__(self, receiver: str, user, token: str):
        subject = (
            f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} Confirm Your Account"
        )
        body = render_template(f"{self.EMAIL_PATH}confirm.txt", user=user, token=token)
        html = render_template(f"{self.EMAIL_PATH}confirm.html", user=user, token=token)
        super().__init__(body, html, subject, receiver)


class ConfirmedUserEmail(Email):
    def __init__(self, receiver: str, user, admin):
        subject = f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} New User Confirmed"
        body = render_template(
            f"{self.EMAIL_PATH}new_confirmation.txt", user=user, admin=admin
        )
        html = render_template(
            f"{self.EMAIL_PATH}new_confirmation.html", user=user, admin=admin
        )
        super().__init__(body, html, subject, receiver)


class ResetPasswordEmail(Email):
    def __init__(self, receiver: str, user, token: str):
        subject = (
            f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} Reset Your Password"
        )
        body = render_template(
            f"{self.EMAIL_PATH}reset_password.txt", user=user, token=token
        )
        html = render_template(
            f"{self.EMAIL_PATH}reset_password.html", user=user, token=token
        )
        super().__init__(body, html, subject, receiver)
