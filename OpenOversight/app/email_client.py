import base64
import os.path
from abc import ABC, abstractmethod
from threading import Thread
from typing import Optional, Self

from flask import current_app
from flask_mail import Mail, Message
from google.oauth2 import service_account
from googleapiclient.discovery import build

from OpenOversight.app.models.emails import Email
from OpenOversight.app.utils.constants import (
    KEY_MAIL_PORT,
    KEY_MAIL_SERVER,
    KEY_OO_HELP_EMAIL,
    KEY_OO_SERVICE_EMAIL,
    SERVICE_ACCOUNT_FILE,
)


class EmailProvider(ABC):
    """Base class to define how emails are sent."""

    @abstractmethod
    def start(self):
        """Set up the email provider."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Determine the required env variables for this provider are configured."""

    @abstractmethod
    def send_email(self, email: Email):
        """Send an email with this email provider."""


class GmailEmailProvider(EmailProvider):
    """Sends email through Gmail using the Google API client."""

    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

    def start(self):
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=self.SCOPES
        )
        delegated_credentials = credentials.with_subject(
            current_app.config[KEY_OO_SERVICE_EMAIL]
        )
        self.service = build("gmail", "v1", credentials=delegated_credentials)

    def is_configured(self) -> bool:
        return (
            os.path.isfile(SERVICE_ACCOUNT_FILE)
            and os.path.getsize(SERVICE_ACCOUNT_FILE) > 0
        )

    def send_email(self, email: Email):
        message = email.create_message()
        resource = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

        (self.service.users().messages().send(userId="me", body=resource).execute())


class SMTPEmailProvider(EmailProvider):
    """Sends email with SMTP using Flask-Mail."""

    def start(self):
        self.mail = Mail(current_app)

    def is_configured(self) -> bool:
        return bool(
            current_app.config.get(KEY_MAIL_SERVER)
            and current_app.config.get(KEY_MAIL_PORT)
        )

    def send_email(self, email: Email):
        app = current_app._get_current_object()
        msg = Message(
            email.subject,
            sender=app.config[KEY_OO_SERVICE_EMAIL],
            recipients=[email.receiver],
            reply_to=app.config[KEY_OO_HELP_EMAIL],
        )
        msg.body = email.body
        msg.html = email.html

        thread = Thread(
            target=SMTPEmailProvider.send_async_email,
            args=[self.mail, app, msg],
        )
        current_app.logger.info("Sent email.")
        thread.start()

    @staticmethod
    def send_async_email(mail: Mail, app, msg: Message):
        with app.app_context():
            mail.send(msg)


class SimulatedEmailProvider(EmailProvider):
    """Writes messages sent with this provider to log for dev/test usage."""

    def start(self):
        if not current_app.debug and not current_app.testing:
            current_app.logger.warning(
                "Using simulated email provider in non-development environment. "
                "Please see CONTRIB.md to set up a email provider."
            )

    def is_configured(self):
        return True

    def send_email(self, email: Email):
        current_app.logger.info("simulated email:\n%s\n%s", email.subject, email.body)


class EmailClient:
    """
    EmailClient is a Singleton class used for sending email. It auto-detects
    the email provider implementation based on whether the required
    configuration is provided for each implementation.
    """

    DEFAULT_PROVIDER: EmailProvider = SimulatedEmailProvider()
    PROVIDER_PRECEDENCE: list[EmailProvider] = [
        GmailEmailProvider(),
        SMTPEmailProvider(),
        DEFAULT_PROVIDER,
    ]

    _provider: Optional[EmailProvider] = None
    _instance: Optional[Self] = None

    def __new__(cls):
        if cls._instance is None:
            cls._provider = cls.auto_detect()
            cls._provider.start()
            current_app.logger.info(
                f"Using email provider: {cls._provider.__class__.__name__}"
            )
            cls._instance = super(EmailClient, cls).__new__(cls)
        return cls._instance

    @classmethod
    def auto_detect(cls):
        """Auto-detect the configured email provider to use for email sending."""
        if current_app.testing:
            return cls.DEFAULT_PROVIDER

        for provider in cls.PROVIDER_PRECEDENCE:
            if provider.is_configured():
                return provider

        raise ValueError("No configured email providers")

    @classmethod
    def send_email(cls, email: Email):
        """
        Deliver the email from the parameter list using the Singleton client.

        :param email: the specific email to be delivered
        """
        if cls._provider is not None:
            cls._provider.send_email(email)
