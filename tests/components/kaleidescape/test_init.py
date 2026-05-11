"""Tests for Kaleidescape config entry."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from . import MOCK_SERIAL
from ._fixtures import (
    mock_config_entry as mock_config_entry_fixture,
    mock_device as mock_device_fixture,
    mock_integration as mock_integration_fixture,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def unload_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_device: MagicMock = Depends(mock_device_fixture),
    mock_integration: MockConfigEntry = Depends(mock_integration_fixture),
) -> None:
    """Test config entry loading and unloading."""
    mock_config_entry = mock_integration
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(mock_device.connect.call_count).to_equal(1)
    expect(mock_device.disconnect.call_count).to_equal(0)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_device.disconnect.call_count).to_equal(1)


@test
async def config_entry_not_ready(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_device: MagicMock = Depends(mock_device_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
) -> None:
    """Test config entry not ready."""
    mock_device.connect.side_effect = ConnectionError

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def disconnect_on_hass_stop(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_device: MagicMock = Depends(mock_device_fixture),
    mock_integration: MockConfigEntry = Depends(mock_integration_fixture),
) -> None:
    """Test device disconnects when Home Assistant stops."""
    expect(mock_integration.state).to_be(ConfigEntryState.LOADED)
    expect(mock_device.disconnect.call_count).to_equal(0)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()

    expect(mock_device.disconnect.call_count).to_equal(1)


@test
async def device(
    _hass: HomeAssistant = Depends(_trigger_executor),
    _integration: MockConfigEntry = Depends(mock_integration_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test device."""
    device = device_registry.async_get_device(
        identifiers={("kaleidescape", MOCK_SERIAL)}
    )
    expect(device is not None).to_be(True)
    expect(device.identifiers).to_equal({("kaleidescape", MOCK_SERIAL)})
