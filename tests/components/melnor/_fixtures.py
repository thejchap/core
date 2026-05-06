"""Tryke fixtures for the melnor integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, _patch, patch

from tryke import fixture

from homeassistant.components.bluetooth.models import BluetoothServiceInfoBleak

from tests.components.bluetooth import generate_advertisement_data, generate_ble_device

FAKE_ADDRESS_1 = "FAKE-ADDRESS-1"
FAKE_ADDRESS_2 = "FAKE-ADDRESS-2"


FAKE_SERVICE_INFO_1 = BluetoothServiceInfoBleak(
    name="YM_TIMER%",
    address=FAKE_ADDRESS_1,
    rssi=-63,
    manufacturer_data={
        13: b"Y\x08\x02\x8f\x00\x00\x00\x00\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0*\x9b\xcf\xbc"
    },
    service_uuids=[],
    service_data={},
    source="local",
    device=generate_ble_device(FAKE_ADDRESS_1, None),
    advertisement=generate_advertisement_data(local_name=""),
    time=0,
    connectable=True,
    tx_power=-127,
)

FAKE_SERVICE_INFO_2 = BluetoothServiceInfoBleak(
    name="YM_TIMER%",
    address=FAKE_ADDRESS_2,
    rssi=-63,
    manufacturer_data={
        13: b"Y\x08\x02\x8f\x00\x00\x00\x00\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0\x00\x00\xf0*\x9b\xcf\xbc"
    },
    service_uuids=[],
    service_data={},
    source="local",
    device=generate_ble_device(FAKE_ADDRESS_2, None),
    advertisement=generate_advertisement_data(local_name=""),
    time=0,
    connectable=True,
    tx_power=-127,
)


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Patch async setup entry to return True."""
    with patch(
        "homeassistant.components.melnor.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


def patch_async_discovered_service_info(
    return_value: list[BluetoothServiceInfoBleak],
) -> _patch:
    """Patch async_discovered_service_info a mocked device info."""
    return patch(
        "homeassistant.components.melnor.config_flow.async_discovered_service_info",
        return_value=return_value,
    )
