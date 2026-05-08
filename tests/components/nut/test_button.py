"""Test the NUT button platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.components.nut.const import INTEGRATION_SUPPORTED_COMMANDS
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .util import async_init_integration

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
async def buttons_ups(
    *,
    model: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Tests that there are no standard buttons."""
    list_commands_return_value = {
        supported_command: supported_command
        for supported_command in INTEGRATION_SUPPORTED_COMMANDS
    }

    await async_init_integration(
        hass,
        model,
        list_commands_return_value=list_commands_return_value,
    )

    button = hass.states.get("button.ups1_power_cycle_outlet_1")
    expect(bool(button)).to_be(False)


@test.skip("translations not compiled in tryke env: entity_id slug mismatch (translation_key=outlet_number_load_cycle)")
async def buttons_pdu_dynamic_outlets(
    *,
    model: str = "EATON-EPDU-G3",
    unique_id_base: str = (
        "EATON_ePDU MA 00U-C IN: TYPE 00A 0P OUT: 00xTYPE_A000A00000_"
    ),
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Tests that the button entities are correct."""
    list_commands_return_value = {
        supported_command: supported_command
        for supported_command in INTEGRATION_SUPPORTED_COMMANDS
    }

    for num in range(1, 25):
        command = f"outlet.{num!s}.load.cycle"
        list_commands_return_value[command] = command

    await async_init_integration(
        hass,
        model,
        list_commands_return_value=list_commands_return_value,
    )

    entity_id = "button.ups1_power_cycle_outlet_a1"
    entry = entity_registry.async_get(entity_id)
    expect(entry).not_.to_be(None)
    expect(entry.unique_id).to_equal(f"{unique_id_base}outlet.1.load.cycle")

    button = hass.states.get(entity_id)
    expect(button).not_.to_be(None)
    expect(button.state).to_equal(STATE_UNKNOWN)

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    button = hass.states.get(entity_id)
    expect(button.state).not_.to_equal(STATE_UNKNOWN)

    button = hass.states.get("button.ups1_power_cycle_outlet_25")
    expect(bool(button)).to_be(False)

    button = hass.states.get("button.ups1_power_cycle_outlet_a25")
    expect(bool(button)).to_be(False)
