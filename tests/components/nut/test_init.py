"""Test init of Nut integration."""

from copy import deepcopy
from unittest.mock import patch

from aionut import NUTError, NUTLoginError
from tryke import Depends, expect, fixture, test

from homeassistant.components.nut.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, device_registry as dr
from homeassistant.setup import async_setup_component

from .util import _get_mock_nutclient, async_init_integration

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    LogCapture,
    area_registry as area_registry_fixture,
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
)
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def config_entry_migrations(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that config entries were migrated."""
    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage"},
        list_ups={"ups1": "UPS 1"},
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 123,
            },
            options={CONF_SCAN_INTERVAL: 30},
        )
        entry.add_to_hass(hass)

        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)

        expect(CONF_SCAN_INTERVAL in entry.options).to_be(False)


@test.skip("translations not compiled in tryke env: sensor entity_id slug mismatch")
async def async_setup_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a successful setup entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "mock", CONF_PORT: "mock"},
    )
    entry.add_to_hass(hass)

    mock_pynut = _get_mock_nutclient(
        list_ups={"ups1": "UPS 1"}, list_vars={"ups.status": "OL"}
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
        expect(entry.state).to_be(ConfigEntryState.LOADED)

        state = hass.states.get("sensor.ups1_status_data")
        expect(state).not_.to_be(None)
        expect(state.state).not_.to_equal(STATE_UNAVAILABLE)
        expect(state.state).to_equal("OL")

        expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
        expect(bool(hass.data.get(DOMAIN))).to_be(False)


@test
async def remove_device_valid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test that we cannot remove a device that still exists."""
    expect(await async_setup_component(hass, "config", {})).to_be(True)

    mock_serial_number = "A00000000000"
    config_entry = await async_init_integration(
        hass,
        username="someuser",
        password="somepassword",
        list_vars={"ups.serial": mock_serial_number},
        list_ups={"ups1": "UPS 1"},
        list_commands_return_value=[],
    )

    device_registry = dr.async_get(hass)
    expect(device_registry).not_.to_be(None)

    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, mock_serial_number)}
    )

    expect(device_entry).not_.to_be(None)
    expect(device_entry.serial_number).to_equal(mock_serial_number)

    client = await hass_ws_client(hass)
    response = await client.remove_device(device_entry.id, config_entry.entry_id)
    expect(bool(response["success"])).to_be(False)


@test
async def remove_device_stale(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test that we can remove a device that no longer exists."""
    expect(await async_setup_component(hass, "config", {})).to_be(True)

    mock_serial_number = "A00000000000"
    config_entry = await async_init_integration(
        hass,
        username="someuser",
        password="somepassword",
        list_vars={"ups.serial": mock_serial_number},
        list_ups={"ups1": "UPS 1"},
        list_commands_return_value=[],
    )

    device_registry = dr.async_get(hass)
    expect(device_registry).not_.to_be(None)

    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "remove-device-id")},
    )

    expect(device_entry).not_.to_be(None)

    client = await hass_ws_client(hass)
    response = await client.remove_device(device_entry.id, config_entry.entry_id)
    expect(bool(response["success"])).to_be(True)

    # Verify that device entry is removed
    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, "remove-device-id")}
    )
    expect(device_entry).to_be(None)


@test.skip("translations not compiled: error log uses translated 'Error fetching UPS state'")
async def config_not_ready(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test for setup failure if connection to broker is missing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "mock", CONF_PORT: "mock"},
    )
    entry.add_to_hass(hass)

    nut_error_message = "Something wrong happened"
    error_message = f"Error fetching UPS state: {nut_error_message}"
    with (
        patch(
            "homeassistant.components.nut.AIONUTClient.list_ups",
            return_value={"ups1"},
        ),
        patch(
            "homeassistant.components.nut.AIONUTClient.list_vars",
            side_effect=NUTError(nut_error_message),
        ),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)

        expect(error_message in caplog.text).to_be(True)


@test.skip("translations not compiled: error log uses translated 'Device authentication error'")
async def auth_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test for setup failure if auth has changed."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "mock", CONF_PORT: "mock"},
    )
    entry.add_to_hass(hass)

    nut_error_message = "Something wrong happened"
    error_message = f"Device authentication error: {nut_error_message}"
    with (
        patch(
            "homeassistant.components.nut.AIONUTClient.list_ups",
            return_value={"ups1"},
        ),
        patch(
            "homeassistant.components.nut.AIONUTClient.list_vars",
            side_effect=NUTLoginError(nut_error_message),
        ),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)

        expect(error_message in caplog.text).to_be(True)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect(flows[0]["context"]["source"]).to_equal("reauth")


@test
async def serial_number(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test for serial number set on device."""
    mock_serial_number = "A00000000000"
    await async_init_integration(
        hass,
        username="someuser",
        password="somepassword",
        list_vars={"ups.serial": mock_serial_number},
        list_ups={"ups1": "UPS 1"},
        list_commands_return_value=[],
    )

    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, mock_serial_number)}
    )

    expect(device_entry).not_.to_be(None)
    expect(device_entry.serial_number).to_equal(mock_serial_number)


@test
async def device_location(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    area_registry: ar.AreaRegistry = Depends(area_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test for suggested location on device."""
    mock_serial_number = "A00000000000"
    mock_device_location = "XYZ Location"
    await async_init_integration(
        hass,
        username="someuser",
        password="somepassword",
        list_vars={
            "ups.serial": mock_serial_number,
            "device.location": mock_device_location,
        },
        list_ups={"ups1": "UPS 1"},
        list_commands_return_value=[],
    )

    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, mock_serial_number)}
    )

    expect(device_entry).not_.to_be(None)
    expect(device_entry.area_id).to_equal(
        area_registry.async_get_area_by_name(mock_device_location).id
    )


@test
async def update_options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test update options triggers reload."""
    mock_pynut = _get_mock_nutclient(
        list_ups={"ups1": "UPS 1"}, list_vars={"ups.status": "OL"}
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        mock_config_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_HOST: "mock",
                CONF_PASSWORD: "somepassword",
                CONF_PORT: "mock",
                CONF_USERNAME: "someuser",
            },
            options={
                "device_options": {
                    "fake_option": "fake_option_value",
                },
            },
        )
        mock_config_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
        expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

        new_options = deepcopy(dict(mock_config_entry.options))
        new_options["device_options"].clear()
        hass.config_entries.async_update_entry(mock_config_entry, options=new_options)
        await hass.async_block_till_done()

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
