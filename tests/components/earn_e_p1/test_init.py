"""Tests for the EARN-E P1 Meter integration setup."""

from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.earn_e_p1.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from ._fixtures import mock_config_entry, mock_listener
from .conftest import MOCK_SERIAL, trigger_callback

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def setup_entry_success(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_listener: MagicMock = Depends(mock_listener),
) -> None:
    """Test successful setup of a config entry."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    mock_listener.start.assert_awaited_once()
    mock_listener.register.assert_called_once()


@test
async def setup_entry_oserror_raises_not_ready(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_listener: MagicMock = Depends(mock_listener),
) -> None:
    """Test that OSError during setup raises ConfigEntryNotReady."""
    mock_listener.start = AsyncMock(side_effect=OSError("Address in use"))

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_listener: MagicMock = Depends(mock_listener),
) -> None:
    """Test unloading a config entry stops the shared listener."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
    mock_listener.unregister.assert_called()
    mock_listener.stop.assert_awaited()


@test.skip("snapshot test — out of scope")
async def device_info() -> None:
    """Stub for test_device_info."""


@test
async def device_registry_not_updated_on_identical_callback(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_listener: MagicMock = Depends(mock_listener),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test device registry is not updated when model/sw_version are unchanged."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    trigger_callback(mock_listener)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, MOCK_SERIAL)})
    expect(device).not_.to_be(None)
    first_modified = device.modified_at

    trigger_callback(mock_listener)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, MOCK_SERIAL)})
    expect(device).not_.to_be(None)
    expect(device.modified_at).to_equal(first_modified)


@test
async def device_registry_updated_on_sw_version_change(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_listener: MagicMock = Depends(mock_listener),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test device registry is updated when sw_version changes."""
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    trigger_callback(mock_listener)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, MOCK_SERIAL)})
    expect(device).not_.to_be(None)
    expect(device.sw_version).to_equal("1.0.0")

    trigger_callback(mock_listener, sw_version="2.0.0")
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, MOCK_SERIAL)})
    expect(device).not_.to_be(None)
    expect(device.sw_version).to_equal("2.0.0")
