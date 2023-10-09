import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import MagicMock, patch

import pytest
from flask import current_app

from OpenOversight.app.email_client import (
    EmailClient,
    GmailEmailProvider,
    SimulatedEmailProvider,
    SMTPEmailProvider,
)
from OpenOversight.app.models.database import User
from OpenOversight.app.models.emails import ChangePasswordEmail, Email
from OpenOversight.app.utils.constants import (
    FILE_TYPE_HTML,
    FILE_TYPE_PLAIN,
    KEY_MAIL_PORT,
    KEY_MAIL_SERVER,
    KEY_OO_HELP_EMAIL,
    KEY_OO_SERVICE_EMAIL,
)
from OpenOversight.tests.constants import ADMIN_USER_EMAIL


def test_email_create_message(faker):
    email_body = faker.paragraph(nb_sentences=5)
    email_html = faker.paragraph(nb_sentences=5)
    email_receiver = faker.ascii_email()
    email_subject = faker.paragraph(nb_sentences=1)

    email = Email(email_body, email_html, email_subject, email_receiver)

    test_message = MIMEMultipart("alternative")
    test_message["To"] = email_receiver
    test_message["From"] = current_app.config[KEY_OO_SERVICE_EMAIL]
    test_message["Subject"] = email_subject
    test_message["Reply-To"] = current_app.config[KEY_OO_HELP_EMAIL]
    test_message.attach(MIMEText(email_body, FILE_TYPE_PLAIN))
    test_message.attach(MIMEText(email_html, FILE_TYPE_HTML))

    actual_message = email.create_message()

    # Make sure both messages use same boundary string
    boundary = "BOUNDARY"
    actual_message.set_boundary(boundary)
    test_message.set_boundary(boundary)

    assert actual_message.as_bytes() == test_message.as_bytes()


def test_email_client_auto_detect_debug_mode(app):
    with app.app_context():
        app.debug = True
        assert isinstance(EmailClient.auto_detect(), SimulatedEmailProvider)


def test_email_client_auto_detect_testing_mode(app):
    with app.app_context():
        app.testing = True
        assert isinstance(EmailClient.auto_detect(), SimulatedEmailProvider)


def test_email_client_auto_detect_follows_precedence(app):
    with app.app_context():
        app.debug = False
        app.testing = False

        provider1 = MagicMock()
        provider1.is_configured.return_value = False
        provider2 = MagicMock()
        provider2.is_configured.return_value = True
        provider3 = MagicMock()
        provider3.is_configured.side_effect = AssertionError(
            "Should not have been called"
        )

        EmailClient.PROVIDER_PRECEDENCE = [provider1, provider2, provider3]
        detected_provider = EmailClient.auto_detect()

        assert detected_provider is provider2
        provider1.is_configured.assert_called_once()
        provider2.is_configured.assert_called_once()
        provider3.is_configured.assert_not_called()


def test_email_client_auto_detect_no_configured_providers_raises_error(app):
    with app.app_context():
        app.debug = False
        app.testing = False

        EmailClient.PROVIDER_PRECEDENCE = []
        with pytest.raises(ValueError):
            EmailClient.auto_detect()


@pytest.mark.parametrize(
    ("is_file", "size", "result"),
    [
        (False, None, False),
        (True, 0, False),
        (True, 100, True),
    ],
)
@patch("os.path.getsize")
@patch("os.path.isfile")
def test_gmail_email_provider_is_configured(
    mock_isfile, mock_getsize, is_file, size, result
):
    mock_getsize.return_value = size
    mock_isfile.return_value = is_file

    assert GmailEmailProvider().is_configured() is result

    mock_isfile.assert_called_once()
    if is_file:
        mock_getsize.assert_called_once()


@pytest.mark.parametrize(
    ("server", "port", "result"),
    [
        (None, None, False),
        ("smtp.example.org", None, False),
        (None, 587, False),
        ("smtp.example.org", 587, True),
    ],
)
def test_smtp_email_provider_is_configured(app, server, port, result):
    with app.app_context():
        app.config[KEY_MAIL_SERVER] = server
        app.config[KEY_MAIL_PORT] = port

        assert SMTPEmailProvider().is_configured() is result


def test_smtp_email_provider_send_email(app, mockdata):
    app.testing = True
    with app.app_context():
        mail = MagicMock()
        user = User.query.first()
        msg = ChangePasswordEmail(ADMIN_USER_EMAIL, user)

        provider = SMTPEmailProvider()
        provider.mail = mail
        provider.send_email(msg)

        time.sleep(0.5)  # wait for async "sending" of email

        mail.send.assert_called_once()
