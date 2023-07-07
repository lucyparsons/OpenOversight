from apiclient import errors
from flask import current_app
from google.oauth2 import service_account
from googleapiclient.discovery import build

from OpenOversight.app.models.emails import Email
from OpenOversight.app.utils.constants import SERVICE_ACCOUNT_FILE


class EmailClient(object):
    """
    EmailClient is a Singleton class that is used for the Gmail client.
    This can be fairly easily switched out with another email service, but it is
    currently defaulted to Gmail.
    """

    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

    _instance = None

    def __new__(cls, dev=False, testing=False):
        if (testing or dev) and cls._instance is None:
            cls._instance = {}

        if cls._instance is None:
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=cls.SCOPES
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
