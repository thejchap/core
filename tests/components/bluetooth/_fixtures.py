"""Tryke fixtures for the bluetooth integration."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import MagicMock, patch

from habluetooth import BaseHaRemoteScanner
from tryke import Depends, fixture

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant

from . import (
    HCI0_SOURCE_ADDRESS,
    HCI1_SOURCE_ADDRESS,
    NON_CONNECTABLE_REMOTE_SOURCE_ADDRESS,
    FakeScanner,
)

from tests.hass_fixtures import (
    enable_bluetooth as enable_bluetooth_fixture,
    hass as hass_fixture,
)


@fixture
def macos_adapter() -> Generator[None]:
    """Fixture that mocks the macos adapter (subset of pytest version)."""
    with (
        patch(
            "homeassistant.components.bluetooth.platform.system",
            return_value="Darwin",
        ),
        patch(
            "habluetooth.scanner.platform.system",
            return_value="Darwin",
        ),
        patch(
            "bluetooth_adapters.systems.platform.system",
            return_value="Darwin",
        ),
        patch("habluetooth.scanner.SYSTEM", "Darwin"),
    ):
        yield


@fixture
def one_adapter() -> Generator[None]:
    """Fixture that mocks one adapter on Linux."""
    with (
        patch(
            "homeassistant.components.bluetooth.platform.system",
            return_value="Linux",
        ),
        patch(
            "habluetooth.scanner.platform.system",
            return_value="Linux",
        ),
        patch(
            "bluetooth_adapters.systems.platform.system",
            return_value="Linux",
        ),
        patch("habluetooth.scanner.SYSTEM", "Linux"),
        patch(
            "bluetooth_adapters.systems.linux.LinuxAdapters.refresh",
        ),
        patch(
            "bluetooth_adapters.systems.linux.LinuxAdapters.adapters",
            {
                "hci0": {
                    "address": "00:00:00:00:00:01",
                    "hw_version": "usb:v1D6Bp0246d053F",
                    "passive_scan": True,
                    "sw_version": "homeassistant",
                    "manufacturer": "ACME",
                    "product": "Bluetooth Adapter 5.0",
                    "product_id": "aa01",
                    "vendor_id": "cc01",
                },
            },
        ),
    ):
        yield


@fixture
async def register_hci0_scanner(
    hass: HomeAssistant = Depends(hass_fixture),
    _enable_bluetooth: None = Depends(enable_bluetooth_fixture),
) -> AsyncGenerator[None]:
    """Register an hci0 scanner."""
    hci0_scanner = FakeScanner(HCI0_SOURCE_ADDRESS, "hci0")
    hci0_scanner.connectable = True
    cancel = bluetooth.async_register_scanner(hass, hci0_scanner, connection_slots=5)
    yield
    cancel()
    bluetooth.async_remove_scanner(hass, hci0_scanner.source)


@fixture
async def register_hci1_scanner(
    hass: HomeAssistant = Depends(hass_fixture),
    _enable_bluetooth: None = Depends(enable_bluetooth_fixture),
) -> AsyncGenerator[None]:
    """Register an hci1 scanner."""
    hci1_scanner = FakeScanner(HCI1_SOURCE_ADDRESS, "hci1")
    hci1_scanner.connectable = True
    cancel = bluetooth.async_register_scanner(hass, hci1_scanner, connection_slots=5)
    yield
    cancel()
    bluetooth.async_remove_scanner(hass, hci1_scanner.source)


@fixture
def disable_new_discovery_flows() -> Generator[MagicMock]:
    """Patch out discovery_flow.async_create_flow so the manager skips it.

    Ported from the pytest ``disable_new_discovery_flows`` fixture in
    ``tests/components/bluetooth/conftest.py``.
    """
    with patch(
        "homeassistant.components.bluetooth.manager.discovery_flow.async_create_flow"
    ) as mock_create_flow:
        yield mock_create_flow


@fixture
async def register_non_connectable_scanner(
    hass: HomeAssistant = Depends(hass_fixture),
    _enable_bluetooth: None = Depends(enable_bluetooth_fixture),
) -> AsyncGenerator[None]:
    """Register a non connectable remote scanner."""
    remote_scanner = BaseHaRemoteScanner(
        NON_CONNECTABLE_REMOTE_SOURCE_ADDRESS, "non connectable", None, False
    )
    cancel = bluetooth.async_register_scanner(hass, remote_scanner)
    yield
    cancel()
    bluetooth.async_remove_scanner(hass, remote_scanner.source)
