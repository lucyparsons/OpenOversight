import os.path
from abc import ABC, abstractmethod
from threading import Thread
from typing import Optional

from flask import current_app
from flask_mail import Mail, Message
from google.oauth2 import service_account
from googleapiclient.discovery import build

from OpenOversight.app.models.emails import Email
from OpenOversight.app.utils.constants import KEY_OO_SERVICE_EMAIL, SERVICE_ACCOUNT_FILE


class EmailProvider(ABC):
    """Base class to define how emails are sent."""

    @abstractmethod
    def start(self):
        """Set up the email provider."""

    @abstractmethod
    def is_configured(self):
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

    def is_configured(self):
        return (
            os.path.isfile(SERVICE_ACCOUNT_FILE)
            and os.path.getsize(SERVICE_ACCOUNT_FILE) > 0
        )

    def send_email(self, email: Email):
        (
            self.service.users()
            .messages()
            .send(userId="me", body=email.create_message())
            .execute()
        )


class SMTPEmailProvider(EmailProvider):
    """Sends email with SMTP using Flask-Mail."""

    CONFIG_SENDER_KEY = "OO_MAIL_SENDER"
    CONFIG_MAIL_SERVER = "MAIL_SERVER"
    CONFIG_MAIL_PORT = "MAIL_PORT"

    def start(self):
        self.mail = Mail()
        self.mail.init_app(current_app)

    def is_configured(self):
        return all(
            key in current_app.config
            for key in [
                self.CONFIG_SENDER_KEY,
                self.CONFIG_MAIL_SERVER,
                self.CONFIG_MAIL_PORT,
            ]
        )

    def send_email(self, email: Email):
        msg = Message(
            email.subject,
            sender=current_app.config["OO_MAIL_SENDER"],
            recipients=[email.receiver],
        )
        msg.body = email.body

        thread = Thread(
            target=SMTPEmailProvider.send_async_email,
            args=[self.mail, current_app, msg],
        )
        current_app.logger.info("Sent email.")
        thread.start()

    @staticmethod
    def send_async_email(mail, app, msg):
        with app.app_context():
            mail.send(msg)


class SimulatedEmailProvider(EmailProvider):
    """Writes messages sent with this provider to log for dev/test usage."""

    def start(self):
        pass

    def is_configured(self):
        return True

    def send_email(self, email: Email):
        current_app.logger.info("simulated email:\n%s\n%s", email.subject, email.body)


class EmailClient:
    """
    EmailClient is a Singleton class used for sending email. It autodetects
    the email provider implementation based on whether the required
    configuration is provided for each implementation.
    """

    DEFAULT_PROVIDER = SimulatedEmailProvider()
    PROVIDER_PRECEDENCE = [
        GmailEmailProvider(),
        SMTPEmailProvider(),
        DEFAULT_PROVIDER,
    ]

    _provider: Optional[EmailProvider] = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._provider = cls.autodetect()
            cls._provider.start()
            current_app.logger.info(f"Using email provider: {cls._provider.__class__}")
            cls._instance = super(EmailClient, cls).__new__(cls)
        return cls._instance

    @classmethod
    def autodetect(cls):
        """Auto-detect the configured email provider to use for email sending."""
        if current_app.debug or current_app.testing:
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
