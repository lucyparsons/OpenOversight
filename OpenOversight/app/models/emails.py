import base64
from email.mime.text import MIMEText

from flask import current_app, render_template

from OpenOversight.app.utils.constants import (
    FILE_TYPE_HTML,
    KEY_OO_MAIL_SUBJECT_PREFIX,
    KEY_OO_SERVICE_EMAIL,
)


class Email:
    """Base class for all emails."""

    def __init__(self, body: str, subject: str, receiver: str):
        self.body = body
        self.receiver = receiver
        self.subject = subject

    def create_message(self):
        message = MIMEText(self.body, FILE_TYPE_HTML)
        message["to"] = self.receiver
        message["from"] = current_app.config[KEY_OO_SERVICE_EMAIL]
        message["subject"] = self.subject
        return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}


class AdministratorApprovalEmail(Email):
    def __init__(self, receiver: str, user, admin):
        subject = (
            f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} New User Registered"
        )
        body = render_template(
            "auth/email/new_registration.html", user=user, admin=admin
        )
        super().__init__(body, subject, receiver)


class ChangeEmailAddressEmail(Email):
    def __init__(self, receiver: str, user, token: str):
        subject = (
            f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} Confirm Your Email "
            f"Address"
        )
        body = render_template("auth/email/change_email.html", user=user, token=token)
        super().__init__(body, subject, receiver)


class ChangePasswordEmail(Email):
    def __init__(self, receiver: str, user):
        subject = f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} Your Password Has Changed"
        body = render_template(
            "auth/email/change_password.html",
            user=user,
            help_email=current_app.config["OO_HELP_EMAIL"],
        )
        super().__init__(body, subject, receiver)


class ConfirmAccountEmail(Email):
    def __init__(self, receiver: str, user, token: str):
        subject = (
            f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} Confirm Your Account"
        )
        body = render_template("auth/email/confirm.html", user=user, token=token)
        super().__init__(body, subject, receiver)


class ConfirmedUserEmail(Email):
    def __init__(self, receiver: str, user, admin):
        subject = f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} New User Confirmed"
        body = render_template(
            "auth/email/new_confirmation.html", user=user, admin=admin
        )
        super().__init__(body, subject, receiver)


class ResetPasswordEmail(Email):
    def __init__(self, receiver: str, user, token: str):
        subject = (
            f"{current_app.config[KEY_OO_MAIL_SUBJECT_PREFIX]} Reset Your Password"
        )
        body = render_template("auth/email/reset_password.html", user=user, token=token)
        super().__init__(body, subject, receiver)
