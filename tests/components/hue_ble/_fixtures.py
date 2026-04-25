"""Tryke fixtures for Hue BLE tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.hue_ble.const import DOMAIN

from . import TEST_DEVICE_MAC, TEST_DEVICE_NAME

from tests.common import MockConfigEntry
from tests.components.bluetooth import generate_ble_device
from tests.hass_fixtures import enable_bluetooth


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.hue_ble.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_ble_device(
    _bluetooth: None = Depends(enable_bluetooth),
) -> Generator[AsyncMock]:
    """Override async_ble_device_from_address."""
    with patch(
        "homeassistant.components.hue_ble.async_ble_device_from_address",
        return_value=generate_ble_device(TEST_DEVICE_NAME, TEST_DEVICE_MAC),
    ) as mock:
        yield mock


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=TEST_DEVICE_NAME,
        unique_id=TEST_DEVICE_MAC.lower(),
        data={},
    )
