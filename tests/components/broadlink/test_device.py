"""Tests for Broadlink devices."""

from collections.abc import AsyncGenerator
from unittest.mock import patch

import broadlink.exceptions as blke
from tryke import Depends, expect, fixture, test

from homeassistant.components.broadlink.const import DOMAIN
from homeassistant.components.broadlink.device import get_domains
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from . import get_device
from ._fixtures import mock_heartbeat as mock_heartbeat_fixture

from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)

DEVICE_FACTORY = "homeassistant.components.broadlink.device.blk.gendevice"


_FAKE_TRANSLATIONS = {
    "component.sensor.entity_component.temperature.name": "Temperature",
    "component.sensor.entity_component.humidity.name": "Humidity",
    "component.sensor.entity_component.aqi.name": "Air quality index",
    "component.sensor.entity_component.illuminance.name": "Illuminance",
    "component.sensor.entity_component.power.name": "Power",
    "component.sensor.entity_component.voltage.name": "Voltage",
    "component.sensor.entity_component.current.name": "Current",
    "component.broadlink.entity.sensor.noise.name": "Noise",
    "component.broadlink.entity.sensor.overload.name": "Overload",
    "component.broadlink.entity.sensor.total_consumption.name": "Total consumption",
    "component.broadlink.entity.sensor.light.name": "Illuminance",
}


async def _fake_get_translations(
    hass_arg, language, category, integrations=None, config_flow=None
):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass_arg, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _heartbeat: None = Depends(mock_heartbeat_fixture),
) -> AsyncGenerator[HomeAssistant]:
    with (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        yield hass


@test
async def device_setup(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test a successful setup."""
    device = get_device("Office")

    with (
        patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward,
        patch.object(hass.config_entries.flow, "async_init") as mock_init,
    ):
        mock_setup = await device.setup_entry(hass)

    expect(mock_setup.entry.state is ConfigEntryState.LOADED).to_be(True)
    expect(mock_setup.api.auth.call_count).to_equal(1)
    expect(mock_setup.api.get_fwversion.call_count).to_equal(1)
    expect(mock_setup.factory.call_count).to_equal(1)

    forward_entries = set(mock_forward.mock_calls[0][1][1])
    domains = get_domains(mock_setup.api.type)
    expect(mock_forward.call_count).to_equal(1)
    expect(forward_entries).to_equal(domains)
    expect(mock_init.call_count).to_equal(0)


@test
async def device_setup_authentication_error(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we handle an authentication error."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()
    mock_api.auth.side_effect = blke.AuthenticationError()

    with (
        patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward,
        patch.object(hass.config_entries.flow, "async_init") as mock_init,
    ):
        mock_setup = await device.setup_entry(hass, mock_api=mock_api)

    expect(mock_setup.entry.state is ConfigEntryState.SETUP_ERROR).to_be(True)
    expect(mock_setup.api.auth.call_count).to_equal(1)
    expect(mock_forward.call_count).to_equal(0)
    expect(mock_init.call_count).to_equal(1)
    expect(mock_init.mock_calls[0][2]["context"]["source"]).to_equal("reauth")
    expect(mock_init.mock_calls[0][2]["data"]).to_equal(
        {"name": device.name, **device.get_entry_data()}
    )


@test
async def device_setup_network_timeout(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we handle a network timeout."""
    device = get_device("Office")
    mock_api = device.get_mock_api()
    mock_api.auth.side_effect = blke.NetworkTimeoutError()

    with (
        patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward,
        patch.object(hass.config_entries.flow, "async_init") as mock_init,
    ):
        mock_setup = await device.setup_entry(hass, mock_api=mock_api)

    expect(mock_setup.entry.state is ConfigEntryState.SETUP_RETRY).to_be(True)
    expect(mock_setup.api.auth.call_count).to_equal(1)
    expect(mock_forward.call_count).to_equal(0)
    expect(mock_init.call_count).to_equal(0)


@test
async def device_setup_os_error(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we handle an OS error."""
    device = get_device("Office")
    mock_api = device.get_mock_api()
    mock_api.auth.side_effect = OSError()

    with (
        patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward,
        patch.object(hass.config_entries.flow, "async_init") as mock_init,
    ):
        mock_setup = await device.setup_entry(hass, mock_api=mock_api)

    expect(mock_setup.entry.state is ConfigEntryState.SETUP_RETRY).to_be(True)
    expect(mock_setup.api.auth.call_count).to_equal(1)
    expect(mock_forward.call_count).to_equal(0)
    expect(mock_init.call_count).to_equal(0)


@test
async def device_setup_broadlink_exception(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we handle a Broadlink exception."""
    device = get_device("Office")
    mock_api = device.get_mock_api()
    mock_api.auth.side_effect = blke.BroadlinkException()

    with (
        patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward,
        patch.object(hass.config_entries.flow, "async_init") as mock_init,
    ):
        mock_setup = await device.setup_entry(hass, mock_api=mock_api)

    expect(mock_setup.entry.state is ConfigEntryState.SETUP_ERROR).to_be(True)
    expect(mock_setup.api.auth.call_count).to_equal(1)
    expect(mock_forward.call_count).to_equal(0)
    expect(mock_init.call_count).to_equal(0)


@test
async def device_setup_update_network_timeout(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we handle a network timeout in the update step."""
    device = get_device("Office")
    mock_api = device.get_mock_api()
    mock_api.check_sensors.side_effect = blke.NetworkTimeoutError()

    with (
        patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward,
        patch.object(hass.config_entries.flow, "async_init") as mock_init,
    ):
        mock_setup = await device.setup_entry(hass, mock_api=mock_api)

    expect(mock_setup.entry.state is ConfigEntryState.SETUP_RETRY).to_be(True)
    expect(mock_setup.api.auth.call_count).to_equal(1)
    expect(mock_setup.api.check_sensors.call_count).to_equal(1)
    expect(mock_forward.call_count).to_equal(0)
    expect(mock_init.call_count).to_equal(0)


@test
async def device_setup_update_authorization_error(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we handle an authorization error in the update step."""
    device = get_device("Office")
    mock_api = device.get_mock_api()
    mock_api.check_sensors.side_effect = (
        blke.AuthorizationError(),
        {"temperature": 30},
    )

    with (
        patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward,
        patch.object(hass.config_entries.flow, "async_init") as mock_init,
    ):
        mock_setup = await device.setup_entry(hass, mock_api=mock_api)

    expect(mock_setup.entry.state is ConfigEntryState.LOADED).to_be(True)
    expect(mock_setup.api.auth.call_count).to_equal(2)
    expect(mock_setup.api.check_sensors.call_count).to_equal(2)

    forward_entries = set(mock_forward.mock_calls[0][1][1])
    domains = get_domains(mock_api.type)
    expect(mock_forward.call_count).to_equal(1)
    expect(forward_entries).to_equal(domains)
    expect(mock_init.call_count).to_equal(0)


@test
async def device_setup_update_authentication_error(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we handle an authentication error in the update step."""
    device = get_device("Garage")
    mock_api = device.get_mock_api()
    mock_api.check_sensors.side_effect = blke.AuthorizationError()
    mock_api.auth.side_effect = (None, blke.AuthenticationError())

    with (
        patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward,
        patch.object(hass.config_entries.flow, "async_init") as mock_init,
    ):
        mock_setup = await device.setup_entry(hass, mock_api=mock_api)

    expect(mock_setup.entry.state is ConfigEntryState.SETUP_RETRY).to_be(True)
    expect(mock_setup.api.auth.call_count).to_equal(2)
    expect(mock_setup.api.check_sensors.call_count).to_equal(1)
    expect(mock_forward.call_count).to_equal(0)
    expect(mock_init.call_count).to_equal(1)
    expect(mock_init.mock_calls[0][2]["context"]["source"]).to_equal("reauth")
    expect(mock_init.mock_calls[0][2]["data"]).to_equal(
        {"name": device.name, **device.get_entry_data()}
    )


@test
async def device_setup_update_broadlink_exception(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we handle a Broadlink exception in the update step."""
    device = get_device("Garage")
    mock_api = device.get_mock_api()
    mock_api.check_sensors.side_effect = blke.BroadlinkException()

    with (
        patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward,
        patch.object(hass.config_entries.flow, "async_init") as mock_init,
    ):
        mock_setup = await device.setup_entry(hass, mock_api=mock_api)

    expect(mock_setup.entry.state is ConfigEntryState.SETUP_RETRY).to_be(True)
    expect(mock_setup.api.auth.call_count).to_equal(1)
    expect(mock_setup.api.check_sensors.call_count).to_equal(1)
    expect(mock_forward.call_count).to_equal(0)
    expect(mock_init.call_count).to_equal(0)


@test
async def device_setup_get_fwversion_broadlink_exception(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we load the device even if we cannot read the firmware version."""
    device = get_device("Office")
    mock_api = device.get_mock_api()
    mock_api.get_fwversion.side_effect = blke.BroadlinkException()

    with patch.object(
        hass.config_entries, "async_forward_entry_setups"
    ) as mock_forward:
        mock_setup = await device.setup_entry(hass, mock_api=mock_api)

    expect(mock_setup.entry.state is ConfigEntryState.LOADED).to_be(True)
    forward_entries = set(mock_forward.mock_calls[0][1][1])
    domains = get_domains(mock_setup.api.type)
    expect(mock_forward.call_count).to_equal(1)
    expect(forward_entries).to_equal(domains)


@test
async def device_setup_get_fwversion_os_error(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we load the device even if we cannot read the firmware version."""
    device = get_device("Office")
    mock_api = device.get_mock_api()
    mock_api.get_fwversion.side_effect = OSError()

    with patch.object(
        hass.config_entries, "async_forward_entry_setups"
    ) as mock_forward:
        mock_setup = await device.setup_entry(hass, mock_api=mock_api)

    expect(mock_setup.entry.state is ConfigEntryState.LOADED).to_be(True)
    forward_entries = set(mock_forward.mock_calls[0][1][1])
    domains = get_domains(mock_setup.api.type)
    expect(mock_forward.call_count).to_equal(1)
    expect(forward_entries).to_equal(domains)


@test
async def device_setup_registry(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we register the device and the entries correctly."""
    device = get_device("Office")

    mock_setup = await device.setup_entry(hass)
    await hass.async_block_till_done()

    expect(len(device_registry.devices)).to_equal(1)

    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, mock_setup.entry.unique_id)}
    )
    expect(device_entry.identifiers).to_equal({(DOMAIN, device.mac)})
    expect(device_entry.name).to_equal(device.name)
    expect(device_entry.model).to_equal(device.model)
    expect(device_entry.manufacturer).to_equal(device.manufacturer)
    expect(device_entry.sw_version).to_equal(device.fwversion)

    for entry in er.async_entries_for_device(entity_registry, device_entry.id):
        expect(
            hass.states.get(entry.entity_id)
            .attributes[ATTR_FRIENDLY_NAME]
            .startswith(device.name)
        ).to_be(True)


@test
async def device_unload_works(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we unload the device."""
    device = get_device("Office")

    with patch.object(hass.config_entries, "async_forward_entry_setups"):
        mock_setup = await device.setup_entry(hass)

    with patch.object(
        hass.config_entries, "async_forward_entry_unload", return_value=True
    ) as mock_forward:
        await hass.config_entries.async_unload(mock_setup.entry.entry_id)

    expect(mock_setup.entry.state is ConfigEntryState.NOT_LOADED).to_be(True)
    forward_entries = {c[1][1] for c in mock_forward.mock_calls}
    domains = get_domains(mock_setup.api.type)
    expect(mock_forward.call_count).to_equal(len(domains))
    expect(forward_entries).to_equal(domains)


@test
async def device_unload_authentication_error(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we unload a device that failed the authentication step."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()
    mock_api.auth.side_effect = blke.AuthenticationError()

    with (
        patch.object(hass.config_entries, "async_forward_entry_setups"),
        patch.object(hass.config_entries.flow, "async_init"),
    ):
        mock_setup = await device.setup_entry(hass, mock_api=mock_api)

    with patch.object(
        hass.config_entries, "async_forward_entry_unload", return_value=True
    ) as mock_forward:
        await hass.config_entries.async_unload(mock_setup.entry.entry_id)

    expect(mock_setup.entry.state is ConfigEntryState.NOT_LOADED).to_be(True)
    expect(mock_forward.call_count).to_equal(0)


@test
async def device_unload_update_failed(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we unload a device that failed the update step."""
    device = get_device("Office")
    mock_api = device.get_mock_api()
    mock_api.check_sensors.side_effect = blke.NetworkTimeoutError()

    with patch.object(hass.config_entries, "async_forward_entry_setups"):
        mock_setup = await device.setup_entry(hass, mock_api=mock_api)

    with patch.object(
        hass.config_entries, "async_forward_entry_unload", return_value=True
    ) as mock_forward:
        await hass.config_entries.async_unload(mock_setup.entry.entry_id)

    expect(mock_setup.entry.state is ConfigEntryState.NOT_LOADED).to_be(True)
    expect(mock_forward.call_count).to_equal(0)


@test
async def device_update_listener(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we update device and entity registry when the entry is renamed."""
    device = get_device("Office")

    mock_setup = await device.setup_entry(hass)
    await hass.async_block_till_done()

    with patch(DEVICE_FACTORY, return_value=mock_setup.api):
        hass.config_entries.async_update_entry(mock_setup.entry, title="New Name")
        await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, mock_setup.entry.unique_id)}
    )
    expect(device_entry.name).to_equal("New Name")
    for entry in er.async_entries_for_device(entity_registry, device_entry.id):
        expect(
            hass.states.get(entry.entity_id)
            .attributes[ATTR_FRIENDLY_NAME]
            .startswith("New Name")
        ).to_be(True)
