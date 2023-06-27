"""This file houses the classes used to send emails."""


class Email:
    def __init__(self, sender: str, receiver: str):
        self.sender = sender
        self.receiver = receiver


class ConfirmEmailAddressEmail(Email):
    def __init__(self, sender: str, receiver: str):
        super.__init__(sender, receiver)
        self.subject = "CONFIRM EMAIL ADDRESS TITLE"
        self.body = "CONFIRM EMAIL ADDRESS BODY"


class ChangeEmailAddressEmail(Email):
    def __init__(self, sender: str, receiver: str):
        super.__init__(sender, receiver)
        self.subject = "CHANGE EMAIL ADDRESS TITLE"
        self.body = "CONFIRM EMAIL ADDRESS BODY"


class ChangePasswordEmail(Email):
    def __init__(self, sender: str, receiver: str):
        super.__init__(sender, receiver)
        self.subject = "CHANGE PASSWORD TITLE"
        self.body = "CHANGE PASSWORD BODY"


class GmailClient(object):
    """GmailClient is a Singleton class that is used for the Gmail client."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("Creating the object")
            cls._instance = super(GmailClient, cls).__new__(cls)
        return cls._instance

    @classmethod
    def send_email(cls):
        pass
