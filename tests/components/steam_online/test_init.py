"""Tests for the Steam component."""

import steam
from tryke import Depends, expect, fixture, test

from homeassistant.components.steam_online.const import DEFAULT_NAME, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from tests.hass_fixtures import device_registry as device_registry_fixture, hass as hass_fixture

from . import create_entry, patch_interface


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def setup(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test unload."""
    entry = create_entry(hass)
    with patch_interface():
        await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.state is ConfigEntryState.LOADED).to_be(True)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(entry.state is ConfigEntryState.NOT_LOADED).to_be(True)
    expect(bool(hass.data.get(DOMAIN))).to_be(False)


@test
async def async_setup_entry_auth_failed(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that it throws ConfigEntryAuthFailed when authentication fails."""
    entry = create_entry(hass)
    with patch_interface() as interface:
        interface.side_effect = steam.api.HTTPError("401")
        await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(entry.state is ConfigEntryState.SETUP_ERROR).to_be(True)
    expect(bool(hass.data.get(DOMAIN))).to_be(False)


@test
async def device_info(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test device info."""
    entry = create_entry(hass)
    with patch_interface():
        await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    device = device_registry.async_get_device(identifiers={(DOMAIN, entry.entry_id)})

    expect(device.configuration_url).to_equal("https://store.steampowered.com")
    expect(device.entry_type).to_equal(dr.DeviceEntryType.SERVICE)
    expect(device.identifiers).to_equal({(DOMAIN, entry.entry_id)})
    expect(device.manufacturer).to_equal(DEFAULT_NAME)
    expect(device.name).to_equal(DEFAULT_NAME)
