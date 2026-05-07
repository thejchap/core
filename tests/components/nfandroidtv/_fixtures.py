"""Tryke fixtures for the nfandroidtv integration."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import fixture

from homeassistant.components.nfandroidtv.const import DOMAIN
from homeassistant.const import CONF_HOST

from . import HOST, NAME

from tests.common import MockConfigEntry


@fixture
def mock_notifications_android_tv() -> Generator[MagicMock]:
    """Mock notifications_android_tv."""
    with patch(
        "homeassistant.components.nfandroidtv.config_flow.Notifications", autospec=True
    ) as mock_client:
        client = mock_client.return_value
        client.cls = mock_client
        yield client


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock Notifications for Android TV / Fire TV configuration entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=NAME,
        data={CONF_HOST: HOST},
        entry_id="123456789",
    )
