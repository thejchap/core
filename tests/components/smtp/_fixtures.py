"""Fixtures for SMTP notify tests."""

from tryke import fixture

from homeassistant.components.smtp.notify import MailNotificationService
from homeassistant.util.ssl import create_client_context


class MockSMTP(MailNotificationService):
    """Test SMTP object that doesn't need a working server."""

    def _send_email(self, msg, recipients):
        """Just return msg string and recipients for testing."""
        return msg.as_string(), recipients


@fixture
def message() -> MockSMTP:
    """Return MockSMTP object with test data."""
    return MockSMTP(
        "localhost",
        25,
        5,
        "test@test.com",
        1,
        "testuser",
        "testpass",
        ["recip1@example.com", "testrecip@test.com"],
        "Home Assistant",
        0,
        True,
        create_client_context(),
    )
