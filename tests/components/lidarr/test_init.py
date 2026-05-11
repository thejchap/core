"""Test Lidarr integration."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.lidarr.const import DEFAULT_NAME, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from ._fixtures import (
    ComponentSetup,
    cannot_connect as cannot_connect_fixture,
    connection as connection_fixture,
    invalid_auth as invalid_auth_fixture,
    setup_integration as setup_integration_fixture,
)

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
async def setup(
    hass: HomeAssistant = Depends(_trigger_executor),
    _connection: None = Depends(connection_fixture),
    setup_integration: ComponentSetup = Depends(setup_integration_fixture),
) -> None:
    """Test setup."""
    await setup_integration()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(hass.data.get(DOMAIN)).to_be(None)


@test
async def async_setup_entry_not_ready(
    hass: HomeAssistant = Depends(_trigger_executor),
    _cannot_connect: None = Depends(cannot_connect_fixture),
    setup_integration: ComponentSetup = Depends(setup_integration_fixture),
) -> None:
    """Test that it throws ConfigEntryNotReady when exception occurs during setup."""
    await setup_integration()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
    expect(hass.data.get(DOMAIN)).to_be(None)


@test
async def async_setup_entry_auth_failed(
    hass: HomeAssistant = Depends(_trigger_executor),
    _invalid_auth: None = Depends(invalid_auth_fixture),
    setup_integration: ComponentSetup = Depends(setup_integration_fixture),
) -> None:
    """Test that it throws ConfigEntryAuthFailed when authentication fails."""
    await setup_integration()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    expect(hass.data.get(DOMAIN)).to_be(None)


@test
async def device_info(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    _connection: None = Depends(connection_fixture),
    setup_integration: ComponentSetup = Depends(setup_integration_fixture),
) -> None:
    """Test device info."""
    await setup_integration()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    await hass.async_block_till_done()
    device = device_registry.async_get_device(identifiers={(DOMAIN, entry.entry_id)})

    expect(device is not None).to_be(True)
    expect(device.configuration_url).to_equal("http://127.0.0.1:8668")
    expect(device.identifiers).to_equal({(DOMAIN, entry.entry_id)})
    expect(device.manufacturer).to_equal(DEFAULT_NAME)
    expect(device.name).to_equal("Mock Title")
    expect(device.sw_version).to_equal("10.0.0.34882")
