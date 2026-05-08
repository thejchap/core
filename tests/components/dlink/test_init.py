"""Test D-Link Smart Plug setup."""

from collections.abc import Awaitable, Callable
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.dlink.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component

from ._fixtures import (
    CONF_DATA,
    config_entry_with_uid as config_entry_with_uid_fixture,
    mocked_plug,
    mocked_plug_legacy,
    mocked_plug_legacy_no_auth,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


type ComponentSetup = Callable[[], Awaitable[None]]


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


def _patch_setup(plug: MagicMock):
    return patch(
        "homeassistant.components.dlink.SmartPlug",
        return_value=plug,
    )


async def _mock_setup_integration(hass: HomeAssistant, plug: MagicMock) -> None:
    """Set up the D-Link integration in Home Assistant."""
    with _patch_setup(plug):
        expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
        await hass.async_block_till_done()


@test
async def setup_config_and_unload(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry_with_uid: MockConfigEntry = Depends(config_entry_with_uid_fixture),
    plug: MagicMock = Depends(mocked_plug),
) -> None:
    """Test setup and unload."""
    await _mock_setup_integration(hass, plug)

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.data).to_equal(CONF_DATA)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(bool(hass.data.get(DOMAIN))).to_be(False)


@test
async def legacy_setup_config_and_unload(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry_with_uid: MockConfigEntry = Depends(config_entry_with_uid_fixture),
    plug: MagicMock = Depends(mocked_plug_legacy),
) -> None:
    """Test legacy setup and unload."""
    await _mock_setup_integration(hass, plug)

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.data).to_equal(CONF_DATA)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(bool(hass.data.get(DOMAIN))).to_be(False)


@test
async def async_setup_entry_not_ready(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry_with_uid: MockConfigEntry = Depends(config_entry_with_uid_fixture),
    mocked_plug_legacy_no_auth: MagicMock = Depends(mocked_plug_legacy_no_auth),
) -> None:
    """Test that it throws ConfigEntryNotReady when exception occurs during legacy setup."""
    with _patch_setup(mocked_plug_legacy_no_auth):
        await hass.config_entries.async_setup(config_entry_with_uid.entry_id)
    expect(config_entry_with_uid.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def device_info(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    config_entry_with_uid: MockConfigEntry = Depends(config_entry_with_uid_fixture),
    plug: MagicMock = Depends(mocked_plug),
) -> None:
    """Test device info."""
    await _mock_setup_integration(hass, plug)

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    device = device_registry.async_get_device(identifiers={(DOMAIN, entry.entry_id)})

    expect(device).not_.to_be(None)
    expect(device.connections).to_equal({("mac", "aa:bb:cc:dd:ee:ff")})
    expect(device.identifiers).to_equal({(DOMAIN, entry.entry_id)})
    expect(device.manufacturer).to_equal("D-Link")
    expect(device.model).to_equal("DSP-W215")
    expect(device.name).to_equal("Mock Title")
