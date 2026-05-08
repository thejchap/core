"""Tests for La Marzocco Bluetooth connection."""

from unittest.mock import MagicMock

from bleak.backends.device import BLEDevice
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant

from . import async_init_integration
from ._fixtures import (
    mock_ble_device,
    mock_ble_device_from_address,
    mock_bluetooth_client,
    mock_cloud_client,
    mock_config_entry_bluetooth,
    mock_generate_installation_key,
    mock_lamarzocco,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    enable_bluetooth as enable_bluetooth_fx,
    hass as hass_fixture,
    mock_bleak_scanner_start,
    mock_bluetooth_adapters,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bt_adapters: None = Depends(mock_bluetooth_adapters),
    _bleak: MagicMock = Depends(mock_bleak_scanner_start),
) -> None:
    """Module-level fixture anchor."""


@test
async def disconnect_on_stop(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _bt: None = Depends(enable_bluetooth_fx),
    _gen_key: MagicMock = Depends(mock_generate_installation_key),
    _cloud: MagicMock = Depends(mock_cloud_client),
    mock_config_entry_bluetooth: MockConfigEntry = Depends(mock_config_entry_bluetooth),
    _ble_device_from_address: MagicMock = Depends(mock_ble_device_from_address),
    mock_bluetooth_client: MagicMock = Depends(mock_bluetooth_client),
) -> None:
    """Test we close the connection with the La Marzocco when HA stops."""
    await async_init_integration(hass, mock_config_entry_bluetooth)
    await hass.async_block_till_done()

    expect(mock_config_entry_bluetooth.state is ConfigEntryState.LOADED).to_be(True)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()

    mock_bluetooth_client.disconnect.assert_awaited_once()


@test.skip("port deferred - sibling test")
async def bluetooth_coordinator_updates_based_on_websocket_state() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def bt_offline_mode_entity_available_when_cloud_fails() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def entity_without_bt_becomes_unavailable_when_cloud_fails_no_bt() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def bluetooth_coordinator_handles_connection_failure() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def bluetooth_coordinator_triggers_entity_updates() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def setup_through_bluetooth_only() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def manual_offline_mode_no_bluetooth_device() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def manual_offline_mode() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def bluetooth_is_set_from_discovery() -> None:
    """Stub."""
