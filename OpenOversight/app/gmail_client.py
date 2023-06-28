"""This file houses the classes used to send emails."""
import base64
from email.mime.text import MIMEText

from apiclient import errors
from flask import current_app, render_template
from google.oauth2 import service_account
from googleapiclient.discovery import build


DEFAULT_SENDER_ADDRESS = "chi-oo@lucyparsonslabs.com"


class Email:
    def __init__(self, body: str, subject: str, receiver: str):
        self.body = body
        self.receiver = receiver
        self.sender = DEFAULT_SENDER_ADDRESS
        self.subject = subject

    @classmethod
    def create_message(cls):
        message = MIMEText(cls.body)
        message["to"] = cls.receiver
        message["from"] = cls.sender
        message["subject"] = cls.subject
        return {"raw": base64.urlsafe_b64encode(message.as_string())}


class AdministratorApprovalEmail(Email):
    def __init__(self, receiver: str, **kwargs):
        app = current_app.app_context()
        subject = f"{app.config['OO_MAIL_SUBJECT_PREFIX']} New User Registered"
        body = render_template("auth/email/new_registration.txt", **kwargs)
        super.__init__(body, subject, receiver)


class ChangeEmailAddressEmail(Email):
    def __init__(self, receiver: str, **kwargs):
        app = current_app.app_context()
        subject = f"{app.config['OO_MAIL_SUBJECT_PREFIX']} 	Confirm Your Email Address"
        body = render_template("auth/email/change_email.txt", **kwargs)
        super.__init__(body, subject, receiver)


class ConfirmAccountEmail(Email):
    def __init__(self, receiver: str, **kwargs):
        app = current_app.app_context()
        subject = f"{app.config['OO_MAIL_SUBJECT_PREFIX']} Confirm Your Account"
        body = render_template("auth/email/confirm.txt", **kwargs)
        super.__init__(body, subject, receiver)


class ConfirmedUserEmail(Email):
    def __init__(self, receiver: str, **kwargs):
        app = current_app.app_context()
        subject = f"{app.config['OO_MAIL_SUBJECT_PREFIX']} New User Confirmed"
        body = render_template("auth/email/new_confirmation.txt", **kwargs)
        super.__init__(body, subject, receiver)


class ResetPasswordEmail(Email):
    def __init__(self, receiver: str, **kwargs):
        app = current_app.app_context()
        subject = f"{app.config['OO_MAIL_SUBJECT_PREFIX']} Reset Your Password"
        body = render_template("auth/email/reset_password.txt", **kwargs)
        super.__init__(body, subject, receiver)


class GmailClient(object):
    """GmailClient is a Singleton class that is used for the Gmail client."""

    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    SERVICE_ACCOUNT_FILE = "service_account_key.json"

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            credentials = service_account.Credentials.from_service_account_file(
                cls.SERVICE_ACCOUNT_FILE, scopes=cls.SCOPES
            )
            delegated_credentials = credentials.with_subject(cls.DEFAULT_SENDER_ADDRESS)
            cls.service = build("gmail", "v1", credentials=delegated_credentials)
            cls._instance = super(GmailClient, cls).__new__(cls)
        return cls._instance

    @classmethod
    def send_email(cls, email: Email):
        app = current_app.app_context()
        if app.env in ("staging", "production"):
            try:
                message = (
                    cls.service.users()
                    .messages()
                    .send(userId="me", body=email.create_message())
                    .execute()
                )
                return message
            except errors.HttpError as error:
                print("An error occurred: %s" % error)
        else:
            app.logger.info("simulated email:\n%s\n%s", email.subject, email.body)
