"""Tryke fixtures for qingping tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_bluetooth_adapters() -> Generator[None]:
    """Mock bluetooth adapters."""
    with (
        patch("habluetooth.util.recover_adapter"),
        patch("bluetooth_auto_recovery.recover_adapter"),
        patch("bluetooth_adapters.systems.platform.system", return_value="Linux"),
        patch("bluetooth_adapters.systems.linux.LinuxAdapters.refresh"),
        patch(
            "bluetooth_adapters.systems.linux.LinuxAdapters.adapters",
            {
                "hci0": {
                    "address": "00:00:00:00:00:01",
                    "hw_version": "usb:v1D6Bp0246d053F",
                    "passive_scan": False,
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
def mock_bleak_scanner_start() -> Generator[MagicMock]:
    """Mock starting the bleak scanner."""
    from habluetooth import (  # noqa: PLC0415
        manager as bluetooth_manager,
        scanner as bluetooth_scanner,
    )

    bluetooth_scanner.OriginalBleakScanner.stop = AsyncMock()  # type: ignore[assignment]

    mock_mgmt_bluetooth_ctl = Mock()
    mock_mgmt_bluetooth_ctl.setup = AsyncMock(return_value=None)

    with (
        patch.object(
            bluetooth_scanner.OriginalBleakScanner,
            "start",
        ) as mock_start,
        patch.object(bluetooth_scanner, "HaScanner"),
        patch.object(
            bluetooth_manager,
            "MGMTBluetoothCtl",
            return_value=mock_mgmt_bluetooth_ctl,
        ),
    ):
        yield mock_start


@fixture
async def enable_bluetooth(
    hass: HomeAssistant = Depends(hass_fixture),
    _scanner: MagicMock = Depends(mock_bleak_scanner_start),
    _adapters: None = Depends(mock_bluetooth_adapters),
) -> AsyncGenerator[None]:
    """Enable bluetooth integration for the test."""
    entry = MockConfigEntry(domain="bluetooth", unique_id="00:00:00:00:00:01")
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    yield
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
