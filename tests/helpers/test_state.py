"""Test state helpers."""

import asyncio
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.lock import LockState
from homeassistant.components.sun import STATE_ABOVE_HORIZON, STATE_BELOW_HORIZON
from homeassistant.const import (
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_CLOSED,
    STATE_HOME,
    STATE_NOT_HOME,
    STATE_OFF,
    STATE_ON,
    STATE_OPEN,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import state

from tests.common import async_mock_service
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def call_to_component(hass: HomeAssistant = Depends(hass)) -> None:
    """Test calls to components state reproduction functions."""
    with patch(
        "homeassistant.components.media_player.reproduce_state.async_reproduce_states"
    ) as media_player_fun:
        media_player_fun.return_value = asyncio.Future()
        media_player_fun.return_value.set_result(None)

        with patch(
            "homeassistant.components.climate.reproduce_state.async_reproduce_states"
        ) as climate_fun:
            climate_fun.return_value = asyncio.Future()
            climate_fun.return_value.set_result(None)

            state_media_player = State("media_player.test", "bad")
            state_climate = State("climate.test", "bad")
            context = "dummy_context"

            await state.async_reproduce_state(
                hass,
                [state_media_player, state_climate],
                context=context,
            )

            media_player_fun.assert_called_once_with(
                hass, [state_media_player], context=context, reproduce_options=None
            )

            climate_fun.assert_called_once_with(
                hass, [state_climate], context=context, reproduce_options=None
            )


@test
async def reproduce_with_no_entity(hass: HomeAssistant = Depends(hass)) -> None:
    """Test reproduce_state with no entity."""
    calls = async_mock_service(hass, "light", SERVICE_TURN_ON)

    await state.async_reproduce_state(hass, State("light.test", "on"))

    await hass.async_block_till_done()

    expect(len(calls)).to_equal(0)
    expect(hass.states.get("light.test")).to_be_none()


@test
async def reproduce_turn_on(hass: HomeAssistant = Depends(hass)) -> None:
    """Test reproduce_state with SERVICE_TURN_ON."""
    calls = async_mock_service(hass, "light", SERVICE_TURN_ON)

    hass.states.async_set("light.test", "off")

    await state.async_reproduce_state(hass, State("light.test", "on"))

    await hass.async_block_till_done()

    expect(len(calls) > 0).to_be(True)
    last_call = calls[-1]
    expect(last_call.domain).to_equal("light")
    expect(last_call.service).to_equal(SERVICE_TURN_ON)
    expect(last_call.data.get("entity_id")).to_equal("light.test")


@test
async def reproduce_turn_off(hass: HomeAssistant = Depends(hass)) -> None:
    """Test reproduce_state with SERVICE_TURN_OFF."""
    calls = async_mock_service(hass, "light", SERVICE_TURN_OFF)

    hass.states.async_set("light.test", "on")

    await state.async_reproduce_state(hass, State("light.test", "off"))

    await hass.async_block_till_done()

    expect(len(calls) > 0).to_be(True)
    last_call = calls[-1]
    expect(last_call.domain).to_equal("light")
    expect(last_call.service).to_equal(SERVICE_TURN_OFF)
    expect(last_call.data.get("entity_id")).to_equal("light.test")


@test
async def reproduce_complex_data(hass: HomeAssistant = Depends(hass)) -> None:
    """Test reproduce_state with complex service data."""
    calls = async_mock_service(hass, "light", SERVICE_TURN_ON)

    hass.states.async_set("light.test", "off")

    complex_data = [255, 100, 100]

    await state.async_reproduce_state(
        hass, State("light.test", "on", {"rgb_color": complex_data})
    )

    await hass.async_block_till_done()

    expect(len(calls) > 0).to_be(True)
    last_call = calls[-1]
    expect(last_call.domain).to_equal("light")
    expect(last_call.service).to_equal(SERVICE_TURN_ON)
    expect(last_call.data.get("rgb_color")).to_equal(complex_data)


@test
async def reproduce_bad_state(hass: HomeAssistant = Depends(hass)) -> None:
    """Test reproduce_state with bad state."""
    calls = async_mock_service(hass, "light", SERVICE_TURN_ON)

    hass.states.async_set("light.test", "off")

    await state.async_reproduce_state(hass, State("light.test", "bad"))

    await hass.async_block_till_done()

    expect(len(calls)).to_equal(0)
    expect(hass.states.get("light.test").state).to_equal("off")


@test
async def as_number_states(hass: HomeAssistant = Depends(hass)) -> None:
    """Test state_as_number with states."""
    zero_states = (
        STATE_OFF,
        STATE_CLOSED,
        LockState.UNLOCKED,
        STATE_BELOW_HORIZON,
        STATE_NOT_HOME,
    )
    one_states = (
        STATE_ON,
        STATE_OPEN,
        LockState.LOCKED,
        STATE_ABOVE_HORIZON,
        STATE_HOME,
    )
    for _state in zero_states:
        expect(state.state_as_number(State("domain.test", _state, {}))).to_equal(0)
    for _state in one_states:
        expect(state.state_as_number(State("domain.test", _state, {}))).to_equal(1)


@test
async def as_number_coercion(hass: HomeAssistant = Depends(hass)) -> None:
    """Test state_as_number with number."""
    for _state in ("0", "0.0", 0, 0.0):
        expect(state.state_as_number(State("domain.test", _state, {}))).to_equal(0.0)
    for _state in ("1", "1.0", 1, 1.0):
        expect(state.state_as_number(State("domain.test", _state, {}))).to_equal(1.0)


@test
async def as_number_invalid_cases(hass: HomeAssistant = Depends(hass)) -> None:
    """Test state_as_number with invalid cases."""
    for _state in ("", "foo", "foo.bar", None, False, True, object, object()):
        expect(
            lambda s=_state: state.state_as_number(State("domain.test", s, {}))
        ).to_raise(ValueError)
