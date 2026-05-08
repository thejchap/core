"""Test the NUT switch platform."""

import json
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.nut.const import DOMAIN, INTEGRATION_SUPPORTED_COMMANDS
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .util import async_init_integration

from tests.common import async_load_fixture
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Force tryke fixture resolution before each test."""


@test.cases(
    test.case("CP1350C", model="CP1350C"),
    test.case("5E650I", model="5E650I"),
    test.case("5E850I", model="5E850I"),
    test.case("CP1500PFCLCD", model="CP1500PFCLCD"),
    test.case("DL650ELCD", model="DL650ELCD"),
    test.case("EATON5P1550", model="EATON5P1550"),
    test.case("blazer_usb", model="blazer_usb"),
)
async def switch_ups(
    *,
    model: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Tests that there are no standard switches."""
    list_commands_return_value = {
        supported_command: supported_command
        for supported_command in INTEGRATION_SUPPORTED_COMMANDS
    }

    await async_init_integration(
        hass,
        model,
        list_commands_return_value=list_commands_return_value,
    )

    switch = hass.states.get("switch.ups1_power_outlet_1")
    expect(bool(switch)).to_be(False)


@test.skip("translations not compiled in tryke env: entity_id slug mismatch (translation_key=outlet_number_load_poweronoff)")
async def switch_pdu_dynamic_outlets(
    *,
    model: str = "EATON-EPDU-G3",
    unique_id_base: str = (
        "EATON_ePDU MA 00U-C IN: TYPE 00A 0P OUT: 00xTYPE_A000A00000"
    ),
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Tests that the switch entities are correct."""
    list_commands_return_value = {
        supported_command: supported_command
        for supported_command in INTEGRATION_SUPPORTED_COMMANDS
    }

    for num in range(1, 25):
        command = f"outlet.{num!s}.load.on"
        list_commands_return_value[command] = command
        command = f"outlet.{num!s}.load.off"
        list_commands_return_value[command] = command

    ups_fixture = f"{model}.json"
    list_vars = json.loads(await async_load_fixture(hass, ups_fixture, DOMAIN))

    run_command = AsyncMock()

    await async_init_integration(
        hass,
        model,
        list_vars=list_vars,
        list_commands_return_value=list_commands_return_value,
        run_command=run_command,
    )

    entity_id = "switch.ups1_power_outlet_a1"
    entry = entity_registry.async_get(entity_id)
    expect(entry).not_.to_be(None)
    expect(entry.unique_id).to_equal(f"{unique_id_base}_outlet.1.load.poweronoff")

    switch = hass.states.get(entity_id)
    expect(switch).not_.to_be(None)
    expect(switch.state).to_equal(STATE_ON)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    run_command.assert_called_with("ups1", "outlet.1.load.off")

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    run_command.assert_called_with("ups1", "outlet.1.load.on")

    switch = hass.states.get("switch.ups1_power_outlet_25")
    expect(bool(switch)).to_be(False)

    switch = hass.states.get("switch.ups1_power_outlet_a25")
    expect(bool(switch)).to_be(False)


@test.skip("translations not compiled in tryke env: entity_id slug mismatch (translation_key=outlet_number_load_poweronoff)")
async def switch_pdu_dynamic_outlets_state_unknown(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test switch entity with missing status is reported as unknown."""
    config_entry = await async_init_integration(
        hass,
        list_ups={"ups1": "UPS 1"},
        list_vars={
            "outlet.count": "1",
            "outlet.1.switchable": "yes",
            "outlet.1.name": "A1",
        },
        list_commands_return_value={
            "outlet.1.load.on": None,
            "outlet.1.load.off": None,
        },
    )

    entity_id = "switch.ups1_power_outlet_a1"
    entry = entity_registry.async_get(entity_id)
    expect(entry).not_.to_be(None)
    expect(entry.unique_id).to_equal(
        f"{config_entry.entry_id}_outlet.1.load.poweronoff"
    )

    switch = hass.states.get(entity_id)
    expect(switch).not_.to_be(None)
    expect(switch.state).to_equal(STATE_UNKNOWN)
