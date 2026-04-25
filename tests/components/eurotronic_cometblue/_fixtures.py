"""Tryke fixtures for the Eurotronic Comet Blue integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from bleak.backends.scanner import AdvertisementData
from tryke import fixture

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.components.eurotronic_cometblue.const import DOMAIN
from homeassistant.const import CONF_ADDRESS
from homeassistant.helpers.device_registry import format_mac

from . import (
    FIXTURE_DEVICE_NAME,
    FIXTURE_MAC,
    FIXTURE_RSSI,
    FIXTURE_SERVICE_UUID,
    FIXTURE_USER_INPUT,
)

from tests.common import MockConfigEntry
from tests.components.bluetooth import generate_ble_device

FAKE_BLE_DEVICE = generate_ble_device(
    address=FIXTURE_MAC, name=FIXTURE_DEVICE_NAME, details={"path": "/dev/test"}
)

FAKE_SERVICE_INFO = BluetoothServiceInfoBleak(
    name=FIXTURE_DEVICE_NAME,
    address=FIXTURE_MAC,
    rssi=FIXTURE_RSSI,
    manufacturer_data={},
    service_data={},
    service_uuids=[FIXTURE_SERVICE_UUID],
    source="local",
    connectable=True,
    time=0,
    device=FAKE_BLE_DEVICE,
    advertisement=AdvertisementData(
        local_name=FIXTURE_DEVICE_NAME,
        manufacturer_data={},
        service_data={},
        service_uuids=[FIXTURE_SERVICE_UUID],
        rssi=FIXTURE_RSSI,
        tx_power=-127,
        platform_data=(),
    ),
    tx_power=-127,
)


@fixture
def mock_service_info() -> Generator[None]:
    """Patch async_discovered_service_info with a mocked device info."""
    with patch(
        "homeassistant.components.eurotronic_cometblue.config_flow.async_discovered_service_info",
        return_value=[FAKE_SERVICE_INFO],
    ):
        yield


@fixture
def mock_ble_device() -> Generator[None]:
    """Mock BLE device."""
    with (
        patch(
            "homeassistant.components.eurotronic_cometblue.async_ble_device_from_address",
            return_value=FAKE_BLE_DEVICE,
        ),
        patch(
            "homeassistant.components.eurotronic_cometblue.config_flow.async_ble_device_from_address",
            return_value=FAKE_BLE_DEVICE,
        ),
    ):
        yield


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Create config entry mock from data."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_ADDRESS: FIXTURE_MAC,
            **FIXTURE_USER_INPUT,
        },
        unique_id=format_mac(FIXTURE_MAC),
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Patch async setup entry to return True."""
    with patch(
        "homeassistant.components.eurotronic_cometblue.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup
