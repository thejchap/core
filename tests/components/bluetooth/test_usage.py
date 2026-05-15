"""Tests for the Bluetooth integration."""

import bleak
from habluetooth.usage import (
    install_multiple_bleak_catcher,
    uninstall_multiple_bleak_catcher,
)
from habluetooth.wrappers import HaBleakClientWrapper, HaBleakScannerWrapper
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import enable_bluetooth as enable_bluetooth_fixture, hass as hass_fixture

from . import generate_ble_device, patch_bleak_backend_type

MOCK_BLE_DEVICE = generate_ble_device(
    "00:00:00:00:00:00",
    "any",
    details={"path": "/dev/hci0/device"},
)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def multiple_bleak_scanner_instances(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test creating multiple BleakScanners without an integration."""
    install_multiple_bleak_catcher()

    instance = bleak.BleakScanner()

    expect(isinstance(instance, HaBleakScannerWrapper)).to_be(True)

    uninstall_multiple_bleak_catcher()

    with patch_bleak_backend_type():
        instance = bleak.BleakScanner()

    expect(isinstance(instance, HaBleakScannerWrapper)).to_be(False)


@test
async def wrapping_bleak_client(
    hass: HomeAssistant = Depends(_trigger_executor),
    _enable_bluetooth: None = Depends(enable_bluetooth_fixture),
) -> None:
    """Test we wrap BleakClient."""
    install_multiple_bleak_catcher()

    instance = bleak.BleakClient(MOCK_BLE_DEVICE)

    expect(isinstance(instance, HaBleakClientWrapper)).to_be(True)

    uninstall_multiple_bleak_catcher()

    instance = bleak.BleakClient(MOCK_BLE_DEVICE)

    expect(isinstance(instance, HaBleakClientWrapper)).to_be(False)
