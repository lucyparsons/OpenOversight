import base64
from email.mime.text import MIMEText

from flask import current_app, render_template

from OpenOversight.app.config import BaseConfig


class Email:
    """Base class for all emails."""

    def __init__(self, body: str, subject: str, receiver: str):
        self.body = body
        self.receiver = receiver
        self.subject = subject

    def create_message(self):
        message = MIMEText(self.body, "html")
        message["to"] = self.receiver
        message["from"] = BaseConfig.OO_SERVICE_EMAIL
        message["subject"] = self.subject
        return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}


class AdministratorApprovalEmail(Email):
    def __init__(self, receiver: str, **kwargs):
        subject = (
            f"{current_app.config.get('OO_MAIL_SUBJECT_PREFIX')} New User Registered"
        )
        body = render_template("auth/email/new_registration.html", **kwargs)
        super().__init__(body, subject, receiver)


class ChangeEmailAddressEmail(Email):
    def __init__(self, receiver: str, **kwargs):
        subject = (
            f"{current_app.config.get('OO_MAIL_SUBJECT_PREFIX')} Confirm Your Email "
            f"Address"
        )
        body = render_template("auth/email/change_email.html", **kwargs)
        super().__init__(body, subject, receiver)


class ConfirmAccountEmail(Email):
    def __init__(self, receiver: str, **kwargs):
        subject = (
            f"{current_app.config.get('OO_MAIL_SUBJECT_PREFIX')} Confirm Your Account"
        )
        body = render_template("auth/email/confirm.html", **kwargs)
        super().__init__(body, subject, receiver)


class ConfirmedUserEmail(Email):
    def __init__(self, receiver: str, **kwargs):
        subject = (
            f"{current_app.config.get('OO_MAIL_SUBJECT_PREFIX')} New User Confirmed"
        )
        body = render_template("auth/email/new_confirmation.html", **kwargs)
        super().__init__(body, subject, receiver)


class ResetPasswordEmail(Email):
    def __init__(self, receiver: str, **kwargs):
        subject = (
            f"{current_app.config.get('OO_MAIL_SUBJECT_PREFIX')} Reset Your Password"
        )
        body = render_template("auth/email/reset_password.html", **kwargs)
        super().__init__(body, subject, receiver)
