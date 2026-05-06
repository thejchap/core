"""Tryke fixtures for Motionblinds Bluetooth tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

from motionblindsble.const import MotionBlindType
from tryke import Depends, fixture

from homeassistant.components.bluetooth.models import BluetoothServiceInfoBleak
from homeassistant.components.motionblinds_ble.const import (
    CONF_BLIND_TYPE,
    CONF_LOCAL_NAME,
    CONF_MAC_CODE,
    DOMAIN,
)
from homeassistant.const import CONF_ADDRESS

from tests.common import MockConfigEntry
from tests.components.bluetooth import generate_advertisement_data, generate_ble_device


@fixture
def address() -> str:
    """Address fixture."""
    return "cc:cc:cc:cc:cc:cc"


@fixture
def mac_code(address: str = Depends(address)) -> str:
    """MAC code fixture."""
    return "".join(address.split(":")[-3:-1]).upper()


@fixture
def display_name(mac_code: str = Depends(mac_code)) -> str:
    """Display name fixture."""
    return f"Motionblind {mac_code.upper()}"


@fixture
def local_name(mac_code: str = Depends(mac_code)) -> str:
    """Local name fixture."""
    return f"MOTION_{mac_code.upper()}"


@fixture
def blind_type() -> MotionBlindType:
    """Blind type fixture."""
    return MotionBlindType.ROLLER


@fixture
def service_info(
    local_name: str = Depends(local_name),
    address: str = Depends(address),
) -> BluetoothServiceInfoBleak:
    """Service info fixture."""
    return BluetoothServiceInfoBleak(
        name=local_name,
        address=address,
        device=generate_ble_device(address=address, name=local_name),
        rssi=-61,
        manufacturer_data={0: b"test"},
        service_data={"test": bytearray(b"0000")},
        service_uuids=["test"],
        source="local",
        advertisement=generate_advertisement_data(
            manufacturer_data={0: b"test"},
            service_uuids=["test"],
        ),
        connectable=True,
        time=0,
        tx_power=-127,
    )


@fixture
def mock_config_entry(
    blind_type: MotionBlindType = Depends(blind_type),
    address: str = Depends(address),
    display_name: str = Depends(display_name),
    mac_code: str = Depends(mac_code),
) -> MockConfigEntry:
    """Config entry fixture."""
    return MockConfigEntry(
        title="mock_title",
        domain=DOMAIN,
        entry_id="mock_entry_id",
        unique_id=address,
        data={
            CONF_ADDRESS: address,
            CONF_LOCAL_NAME: display_name,
            CONF_MAC_CODE: mac_code,
            CONF_BLIND_TYPE: blind_type.name.lower(),
        },
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.motionblinds_ble.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def motionblinds_ble_connect(
    local_name: str = Depends(local_name),
    address: str = Depends(address),
) -> Generator[tuple[AsyncMock, Mock]]:
    """Mock motion blinds ble connection and entry setup."""
    device = Mock()
    device.name = local_name
    device.address = address

    bleak_scanner = AsyncMock()
    bleak_scanner.discover.return_value = [device]

    with (
        patch(
            "homeassistant.components.motionblinds_ble.config_flow.bluetooth.async_scanner_count",
            return_value=1,
        ),
        patch(
            "homeassistant.components.motionblinds_ble.config_flow.bluetooth.async_get_scanner",
            return_value=bleak_scanner,
        ),
    ):
        yield bleak_scanner, device
