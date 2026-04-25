"""Tryke fixtures for OpenDisplay tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.opendisplay.const import CONF_ENCRYPTION_KEY, DOMAIN

from . import (
    DEVICE_CONFIG,
    ENCRYPTION_KEY,
    FIRMWARE_VERSION,
    TEST_ADDRESS,
    TEST_TITLE,
)

from tests.common import MockConfigEntry
from tests.components.bluetooth import generate_ble_device


@fixture
def mock_ble_device() -> Generator[None]:
    """Mock the BLE device being visible."""
    ble_device = generate_ble_device(TEST_ADDRESS, TEST_TITLE)
    with (
        patch(
            "homeassistant.components.opendisplay.async_ble_device_from_address",
            return_value=ble_device,
        ),
        patch(
            "homeassistant.components.opendisplay.config_flow.async_ble_device_from_address",
            return_value=ble_device,
        ),
        patch(
            "homeassistant.components.opendisplay.services.async_ble_device_from_address",
            return_value=ble_device,
        ),
    ):
        yield


@fixture
def mock_opendisplay_device_class() -> Generator[MagicMock]:
    """Yield the OpenDisplayDevice class mock."""
    with (
        patch(
            "homeassistant.components.opendisplay.OpenDisplayDevice",
            autospec=True,
        ) as mock_class,
        patch(
            "homeassistant.components.opendisplay.config_flow.OpenDisplayDevice",
            new=mock_class,
        ),
        patch(
            "homeassistant.components.opendisplay.services.OpenDisplayDevice",
            new=mock_class,
        ),
    ):
        mock_device = mock_class.return_value
        mock_device.__aenter__.return_value = mock_device
        mock_device.read_firmware_version.return_value = FIRMWARE_VERSION
        mock_device.config = DEVICE_CONFIG
        mock_device.is_flex = True
        yield mock_class


@fixture
def mock_opendisplay_device(
    cls_mock: MagicMock = Depends(mock_opendisplay_device_class),
) -> MagicMock:
    """Mock the OpenDisplayDevice instance."""
    return cls_mock.return_value


@fixture
def mock_setup_entry() -> Generator[None]:
    """Prevent the integration from actually setting up after config flow."""
    with patch(
        "homeassistant.components.opendisplay.async_setup_entry",
        return_value=True,
    ):
        yield


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_ADDRESS,
        title=TEST_TITLE,
        data={},
    )


@fixture
def mock_encrypted_config_entry() -> MockConfigEntry:
    """Create a mock config entry with an encryption key."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_ADDRESS,
        title=TEST_TITLE,
        data={CONF_ENCRYPTION_KEY: ENCRYPTION_KEY},
    )
