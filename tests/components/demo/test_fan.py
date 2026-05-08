"""Test cases around the demo fan platform."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import fan
from homeassistant.components.demo.fan import (
    PRESET_MODE_AUTO,
    PRESET_MODE_ON,
    PRESET_MODE_SLEEP,
    PRESET_MODE_SMART,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ENTITY_MATCH_ALL,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import setup_homeassistant

from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def fan_only() -> Generator[None]:
    """Enable only the fan platform."""
    with patch(
        "homeassistant.components.demo.COMPONENTS_WITH_CONFIG_ENTRY_DEMO_PLATFORM",
        [Platform.FAN],
    ):
        yield


@fixture
async def setup_comp(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_ha: None = Depends(setup_homeassistant),
    _fan_only: None = Depends(fan_only),
) -> None:
    """Initialize components."""
    expect(
        await async_setup_component(hass, fan.DOMAIN, {"fan": {"platform": "demo"}})
    ).to_be(True)
    await hass.async_block_till_done()


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_comp: None = Depends(setup_comp),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


# Helpers used by tests below.
async def _check_turn_on(hass: HomeAssistant, entity_id: str) -> None:
    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_OFF)
    await hass.services.async_call(
        fan.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_ON)


@test
async def turn_on_living_room_fan(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turning on the living room fan."""
    await _check_turn_on(hass, "fan.living_room_fan")


@test
async def turn_on_percentage_full_fan(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turning on the percentage full fan."""
    await _check_turn_on(hass, "fan.percentage_full_fan")


@test
async def turn_on_ceiling_fan(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turning on the ceiling fan."""
    await _check_turn_on(hass, "fan.ceiling_fan")


@test
async def turn_on_percentage_limited_fan(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turning on the percentage limited fan."""
    await _check_turn_on(hass, "fan.percentage_limited_fan")


async def _check_turn_on_with_speed_and_percentage(
    hass: HomeAssistant, fan_entity_id: str
) -> None:
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)
    await hass.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 100},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[fan.ATTR_PERCENTAGE]).to_equal(100)

    await hass.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 0},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[fan.ATTR_PERCENTAGE]).to_equal(0)


@test
async def turn_on_with_speed_and_percentage_living_room(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turning on with speed and percentage for living room fan."""
    await _check_turn_on_with_speed_and_percentage(hass, "fan.living_room_fan")


@test
async def turn_on_with_speed_and_percentage_full(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turning on with speed and percentage for percentage full fan."""
    await _check_turn_on_with_speed_and_percentage(hass, "fan.percentage_full_fan")


@test
async def turn_on_with_preset_mode_only(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turning on with preset mode only."""
    fan_entity_id = "fan.preset_only_limited_fan"
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)
    await hass.services.async_call(
        fan.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: PRESET_MODE_AUTO},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[fan.ATTR_PRESET_MODE]).to_equal(PRESET_MODE_AUTO)
    expect(state.attributes[fan.ATTR_PRESET_MODES]).to_equal(
        [PRESET_MODE_AUTO, PRESET_MODE_SMART, PRESET_MODE_SLEEP, PRESET_MODE_ON]
    )

    await hass.services.async_call(
        fan.DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: fan_entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[fan.ATTR_PRESET_MODE]).to_be(None)


async def _check_turn_off(hass: HomeAssistant, fan_entity_id: str) -> None:
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)
    await hass.services.async_call(
        fan.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: fan_entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_ON)
    await hass.services.async_call(
        fan.DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: fan_entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)


@test
async def turn_off(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turning off all fans (covers all entity IDs)."""
    for fan_entity_id in (
        "fan.living_room_fan",
        "fan.percentage_full_fan",
        "fan.ceiling_fan",
        "fan.percentage_limited_fan",
    ):
        await _check_turn_off(hass, fan_entity_id)


@test
async def turn_off_without_entity_id(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turning off all fans via match_all."""
    fan_entity_id = "fan.living_room_fan"
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)

    await hass.services.async_call(
        fan.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: fan_entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_ON)

    await hass.services.async_call(
        fan.DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_MATCH_ALL}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)


@test
async def set_direction(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the direction of the device."""
    fan_entity_id = "fan.living_room_fan"
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_SET_DIRECTION,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_DIRECTION: fan.DIRECTION_REVERSE},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    expect(state.attributes[fan.ATTR_DIRECTION]).to_equal(fan.DIRECTION_REVERSE)


@test
async def set_preset_mode(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the preset mode of the device."""
    fan_entity_id = "fan.living_room_fan"
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: PRESET_MODE_AUTO},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[fan.ATTR_PRESET_MODE]).to_equal(PRESET_MODE_AUTO)


@test
async def set_preset_mode_invalid(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting an invalid preset mode for the device."""
    fan_entity_id = "fan.living_room_fan"
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)

    async with expect_raises_async(fan.NotValidPresetModeError):
        await hass.services.async_call(
            fan.DOMAIN,
            fan.SERVICE_SET_PRESET_MODE,
            {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: "invalid"},
            blocking=True,
        )

    async with expect_raises_async(fan.NotValidPresetModeError):
        await hass.services.async_call(
            fan.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PRESET_MODE: "invalid"},
            blocking=True,
        )


@test
async def set_percentage(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the percentage speed of the device."""
    fan_entity_id = "fan.living_room_fan"
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE: 33},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    expect(state.attributes[fan.ATTR_PERCENTAGE]).to_equal(33)


@test
async def increase_decrease_speed(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test increasing and decreasing the percentage speed of the device."""
    fan_entity_id = "fan.living_room_fan"
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[fan.ATTR_PERCENTAGE_STEP]).to_equal(100 / 3)

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_INCREASE_SPEED,
        {ATTR_ENTITY_ID: fan_entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    expect(state.attributes[fan.ATTR_PERCENTAGE]).to_equal(33)

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_DECREASE_SPEED,
        {ATTR_ENTITY_ID: fan_entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    expect(state.attributes[fan.ATTR_PERCENTAGE]).to_equal(0)


@test
async def increase_decrease_speed_with_percentage_step(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test increasing speed with a percentage step."""
    fan_entity_id = "fan.percentage_full_fan"
    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_INCREASE_SPEED,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_PERCENTAGE_STEP: 25},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    expect(state.attributes[fan.ATTR_PERCENTAGE]).to_equal(25)


@test
async def oscillate(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test oscillating the fan."""
    fan_entity_id = "fan.living_room_fan"
    state = hass.states.get(fan_entity_id)
    expect(state.state).to_equal(STATE_OFF)
    expect(bool(state.attributes.get(fan.ATTR_OSCILLATING))).to_be(False)

    await hass.services.async_call(
        fan.DOMAIN,
        fan.SERVICE_OSCILLATE,
        {ATTR_ENTITY_ID: fan_entity_id, fan.ATTR_OSCILLATING: True},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(fan_entity_id)
    expect(state.attributes[fan.ATTR_OSCILLATING]).to_be(True)


@test
async def is_on(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test is on service call."""
    fan_entity_id = "fan.living_room_fan"
    expect(fan.is_on(hass, fan_entity_id)).to_be(False)

    await hass.services.async_call(
        fan.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: fan_entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    expect(fan.is_on(hass, fan_entity_id)).to_be(True)
