"""The tests for the litejet component."""

from unittest.mock import Mock

from tryke import Depends, expect, fixture, test

from homeassistant.components import switch
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant

from . import async_init_integration
from ._fixtures import mock_litejet as mock_litejet_fixture

from tests.hass_fixtures import hass as hass_fixture, mock_network

ENTITY_SWITCH = "switch.mock_switch_1"
ENTITY_SWITCH_NUMBER = 1
ENTITY_OTHER_SWITCH = "switch.mock_switch_2"
ENTITY_OTHER_SWITCH_NUMBER = 2


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def on_off(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_litejet: Mock = Depends(mock_litejet_fixture),
) -> None:
    """Test turning the switch on and off."""
    await async_init_integration(hass, use_switch=True)

    expect(hass.states.get(ENTITY_SWITCH).state).to_equal(STATE_OFF)
    expect(hass.states.get(ENTITY_OTHER_SWITCH).state).to_equal(STATE_OFF)

    expect(switch.is_on(hass, ENTITY_SWITCH)).to_be(False)

    await hass.services.async_call(
        switch.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_SWITCH}, blocking=True
    )
    mock_litejet.press_switch.assert_called_with(ENTITY_SWITCH_NUMBER)

    await hass.services.async_call(
        switch.DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_SWITCH}, blocking=True
    )
    mock_litejet.release_switch.assert_called_with(ENTITY_SWITCH_NUMBER)


@test
async def pressed_event(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_litejet: Mock = Depends(mock_litejet_fixture),
) -> None:
    """Test handling an event from LiteJet."""
    await async_init_integration(hass, use_switch=True)

    mock_litejet.switch_pressed_callbacks[ENTITY_SWITCH_NUMBER]()
    await hass.async_block_till_done()

    expect(switch.is_on(hass, ENTITY_SWITCH)).to_be(True)
    expect(switch.is_on(hass, ENTITY_OTHER_SWITCH)).to_be(False)
    expect(hass.states.get(ENTITY_SWITCH).state).to_equal(STATE_ON)
    expect(hass.states.get(ENTITY_OTHER_SWITCH).state).to_equal(STATE_OFF)

    mock_litejet.switch_pressed_callbacks[ENTITY_OTHER_SWITCH_NUMBER]()
    await hass.async_block_till_done()

    expect(switch.is_on(hass, ENTITY_OTHER_SWITCH)).to_be(True)
    expect(switch.is_on(hass, ENTITY_SWITCH)).to_be(True)
    expect(hass.states.get(ENTITY_SWITCH).state).to_equal(STATE_ON)
    expect(hass.states.get(ENTITY_OTHER_SWITCH).state).to_equal(STATE_ON)


@test
async def released_event(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_litejet: Mock = Depends(mock_litejet_fixture),
) -> None:
    """Test handling an event from LiteJet."""
    await async_init_integration(hass, use_switch=True)

    mock_litejet.switch_pressed_callbacks[ENTITY_OTHER_SWITCH_NUMBER]()
    await hass.async_block_till_done()

    expect(switch.is_on(hass, ENTITY_OTHER_SWITCH)).to_be(True)

    mock_litejet.switch_released_callbacks[ENTITY_OTHER_SWITCH_NUMBER]()
    await hass.async_block_till_done()

    expect(switch.is_on(hass, ENTITY_OTHER_SWITCH)).to_be(False)
    expect(switch.is_on(hass, ENTITY_SWITCH)).to_be(False)
    expect(hass.states.get(ENTITY_SWITCH).state).to_equal(STATE_OFF)
    expect(hass.states.get(ENTITY_OTHER_SWITCH).state).to_equal(STATE_OFF)


@test
async def connected_event(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_litejet: Mock = Depends(mock_litejet_fixture),
) -> None:
    """Test handling an event from LiteJet."""
    await async_init_integration(hass, use_switch=True)

    expect(hass.states.get(ENTITY_SWITCH).state).to_equal(STATE_OFF)
    expect(hass.states.get(ENTITY_OTHER_SWITCH).state).to_equal(STATE_OFF)

    mock_litejet.connected_changed(False, "test")
    await hass.async_block_till_done()

    expect(hass.states.get(ENTITY_SWITCH).state).to_equal(STATE_UNAVAILABLE)
    expect(hass.states.get(ENTITY_OTHER_SWITCH).state).to_equal(STATE_UNAVAILABLE)

    mock_litejet.connected_changed(True, None)
    await hass.async_block_till_done()

    expect(hass.states.get(ENTITY_SWITCH).state).to_equal(STATE_OFF)
    expect(hass.states.get(ENTITY_OTHER_SWITCH).state).to_equal(STATE_OFF)
