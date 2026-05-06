"""Tryke fixtures for the Fully Kiosk Browser integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from homeassistant.components.fully_kiosk.const import DOMAIN
from homeassistant.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_SSL,
    CONF_VERIFY_SSL,
)

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Test device",
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "mocked-password",
            CONF_MAC: "aa:bb:cc:dd:ee:ff",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        },
        unique_id="12345",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.fully_kiosk.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_fully_kiosk_config_flow() -> Generator[MagicMock]:
    """Return a mocked Fully Kiosk client for the config flow."""
    with patch(
        "homeassistant.components.fully_kiosk.config_flow.FullyKiosk",
        autospec=True,
    ) as client_mock:
        client = client_mock.return_value
        client.getDeviceInfo.return_value = {
            "deviceName": "Test device",
            "deviceID": "12345",
            "Mac": "AA:BB:CC:DD:EE:FF",
        }
        yield client
