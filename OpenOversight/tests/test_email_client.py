from unittest.mock import MagicMock

import pytest

from OpenOversight.app.email_client import EmailClient, SimulatedEmailProvider


def test_autodetect_debug_mode(app):
    with app.app_context():
        app.debug = True
        assert isinstance(EmailClient.autodetect(), SimulatedEmailProvider)


def test_autodetect_testing_mode(app):
    with app.app_context():
        app.testing = True
        assert isinstance(EmailClient.autodetect(), SimulatedEmailProvider)


def test_autodetect_follows_precedence(app):
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
        detected_provider = EmailClient.autodetect()

        assert detected_provider is provider2
        provider1.is_configured.assert_called_once()
        provider2.is_configured.assert_called_once()
        provider3.is_configured.assert_not_called()


def test_autodetect_no_configured_providers(app):
    with app.app_context():
        app.debug = False
        app.testing = False

        EmailClient.PROVIDER_PRECEDENCE = []
        with pytest.raises(ValueError):
            EmailClient.autodetect()
