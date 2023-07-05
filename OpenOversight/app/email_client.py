import base64
import os
from email.mime.text import MIMEText

from apiclient import errors
from flask import current_app, render_template
from google.oauth2 import service_account
from googleapiclient.discovery import build


class Email:
    """Base class for all emails."""

    def __init__(self, body: str, subject: str, receiver: str):
        self.body = body
        self.receiver = receiver
        self.subject = subject

    def create_message(self):
        message = MIMEText(self.body, "html")
        message["to"] = self.receiver
        message["from"] = current_app.config["OO_SERVICE_EMAIL"]
        message["subject"] = self.subject
        return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}


class AdministratorApprovalEmail(Email):
    def __init__(self, receiver: str, user, admin):
        subject = (
            f"{current_app.config.get('OO_MAIL_SUBJECT_PREFIX')} New User Registered"
        )
        body = render_template(
            "auth/email/new_registration.html", user=user, admin=admin
        )
        super().__init__(body, subject, receiver)


class ChangeEmailAddressEmail(Email):
    def __init__(self, receiver: str, user, token: str):
        subject = (
            f"{current_app.config.get('OO_MAIL_SUBJECT_PREFIX')} Confirm Your Email "
            f"Address"
        )
        body = render_template("auth/email/change_email.html", user=user, token=token)
        super().__init__(body, subject, receiver)


class ConfirmAccountEmail(Email):
    def __init__(self, receiver: str, user, token: str):
        subject = (
            f"{current_app.config.get('OO_MAIL_SUBJECT_PREFIX')} Confirm Your Account"
        )
        body = render_template("auth/email/confirm.html", user=user, token=token)
        super().__init__(body, subject, receiver)


class ConfirmedUserEmail(Email):
    def __init__(self, receiver: str, user, admin):
        subject = (
            f"{current_app.config.get('OO_MAIL_SUBJECT_PREFIX')} New User Confirmed"
        )
        body = render_template(
            "auth/email/new_confirmation.html", user=user, admin=admin
        )
        super().__init__(body, subject, receiver)


class ResetPasswordEmail(Email):
    def __init__(self, receiver: str, user, token: str):
        subject = (
            f"{current_app.config.get('OO_MAIL_SUBJECT_PREFIX')} Reset Your Password"
        )
        body = render_template("auth/email/reset_password.html", user=user, token=token)
        super().__init__(body, subject, receiver)


class EmailClient(object):
    """
    EmailClient is a Singleton class that is used for the Gmail client.
    This can be fairly easily switched out with another email service, but it is
    currently defaulted to Gmail.
    """

    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    SERVICE_ACCOUNT_FILE = "service_account_key.json"

    _instance = None

    def __new__(cls, testing=False):
        service_account_file_size = os.path.getsize(cls.SERVICE_ACCOUNT_FILE)

        if (testing or service_account_file_size == 0) and cls._instance is None:
            cls._instance = {}

        if cls._instance is None:
            credentials = service_account.Credentials.from_service_account_file(
                cls.SERVICE_ACCOUNT_FILE, scopes=cls.SCOPES
            )
            delegated_credentials = credentials.with_subject(
                current_app.config["OO_SERVICE_EMAIL"]
            )
            cls.service = build("gmail", "v1", credentials=delegated_credentials)
            cls._instance = super(EmailClient, cls).__new__(cls)
        return cls._instance

    @classmethod
    def send_email(cls, email: Email):
        """
        Deliver the email from the parameter list using the Singleton client.

        :param email: the specific email to be delivered
        """
        if not cls._instance:
            current_app.logger.info(
                "simulated email:\n%s\n%s", email.subject, email.body
            )
        else:
            try:
                (
                    cls.service.users()
                    .messages()
                    .send(userId="me", body=email.create_message())
                    .execute()
                )
            except errors.HttpError as error:
                print("An error occurred: %s" % error)
