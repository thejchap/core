"""The tests for the demo water_heater component."""

from collections.abc import Generator
from unittest.mock import patch

import voluptuous as vol

from tryke import Depends, expect, fixture, test

from homeassistant.components import water_heater
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

from ._fixtures import setup_homeassistant

from tests.components.water_heater import common
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async

ENTITY_WATER_HEATER = "water_heater.demo_water_heater"
ENTITY_WATER_HEATER_CELSIUS = "water_heater.demo_water_heater_celsius"


@fixture
def water_heater_only() -> Generator[None]:
    """Enable only the water_heater platform."""
    with patch(
        "homeassistant.components.demo.COMPONENTS_WITH_CONFIG_ENTRY_DEMO_PLATFORM",
        [Platform.WATER_HEATER],
    ):
        yield


@fixture
async def setup_comp(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_ha: None = Depends(setup_homeassistant),
    _water_heater_only: None = Depends(water_heater_only),
) -> None:
    """Set up demo component."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    expect(
        await async_setup_component(
            hass, water_heater.DOMAIN, {"water_heater": {"platform": "demo"}}
        )
    ).to_be(True)
    await hass.async_block_till_done()


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_comp: None = Depends(setup_comp),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def setup_params(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the initial parameters."""
    state = hass.states.get(ENTITY_WATER_HEATER)
    expect(state.attributes.get("temperature")).to_equal(119)
    expect(state.attributes.get("away_mode")).to_equal("off")
    expect(state.attributes.get("operation_mode")).to_equal("eco")
    expect(state.attributes.get("target_temp_step")).to_equal(1)


@test
async def default_setup_params(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setup with default parameters."""
    state = hass.states.get(ENTITY_WATER_HEATER)
    expect(state.attributes.get("min_temp")).to_equal(110)
    expect(state.attributes.get("max_temp")).to_equal(140)


@test
async def set_only_target_temp_bad_attr(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the target temperature without required attribute."""
    state = hass.states.get(ENTITY_WATER_HEATER)
    expect(state.attributes.get("temperature")).to_equal(119)
    async with expect_raises_async(vol.Invalid):
        await common.async_set_temperature(hass, None, ENTITY_WATER_HEATER)
    expect(state.attributes.get("temperature")).to_equal(119)


@test
async def set_only_target_temp(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setting of the target temperature."""
    state = hass.states.get(ENTITY_WATER_HEATER)
    expect(state.attributes.get("temperature")).to_equal(119)
    await common.async_set_temperature(hass, 110, ENTITY_WATER_HEATER)
    state = hass.states.get(ENTITY_WATER_HEATER)
    expect(state.attributes.get("temperature")).to_equal(110)


@test
async def set_operation_bad_attr_and_state(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting operation mode without required attribute."""
    state = hass.states.get(ENTITY_WATER_HEATER)
    expect(state.attributes.get("operation_mode")).to_equal("eco")
    expect(state.state).to_equal("eco")
    async with expect_raises_async(vol.Invalid):
        await common.async_set_operation_mode(hass, None, ENTITY_WATER_HEATER)
    state = hass.states.get(ENTITY_WATER_HEATER)
    expect(state.attributes.get("operation_mode")).to_equal("eco")
    expect(state.state).to_equal("eco")


@test
async def set_operation(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting of new operation mode."""
    state = hass.states.get(ENTITY_WATER_HEATER)
    expect(state.attributes.get("operation_mode")).to_equal("eco")
    expect(state.state).to_equal("eco")
    await common.async_set_operation_mode(hass, "electric", ENTITY_WATER_HEATER)
    state = hass.states.get(ENTITY_WATER_HEATER)
    expect(state.attributes.get("operation_mode")).to_equal("electric")
    expect(state.state).to_equal("electric")


@test
async def set_away_mode_bad_attr(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the away mode without required attribute."""
    state = hass.states.get(ENTITY_WATER_HEATER)
    expect(state.attributes.get("away_mode")).to_equal("off")
    async with expect_raises_async(vol.Invalid):
        await common.async_set_away_mode(hass, None, ENTITY_WATER_HEATER)
    expect(state.attributes.get("away_mode")).to_equal("off")


@test
async def set_away_mode_on(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the away mode on/true."""
    await common.async_set_away_mode(hass, True, ENTITY_WATER_HEATER)
    state = hass.states.get(ENTITY_WATER_HEATER)
    expect(state.attributes.get("away_mode")).to_equal("on")


@test
async def set_away_mode_off(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the away mode off/false."""
    await common.async_set_away_mode(hass, False, ENTITY_WATER_HEATER_CELSIUS)
    state = hass.states.get(ENTITY_WATER_HEATER_CELSIUS)
    expect(state.attributes.get("away_mode")).to_equal("off")


@test
async def set_only_target_temp_with_convert(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setting of the target temperature."""
    state = hass.states.get(ENTITY_WATER_HEATER_CELSIUS)
    expect(state.attributes.get("temperature")).to_equal(113)
    await common.async_set_temperature(hass, 114, ENTITY_WATER_HEATER_CELSIUS)
    state = hass.states.get(ENTITY_WATER_HEATER_CELSIUS)
    expect(state.attributes.get("temperature")).to_equal(114)


@test
async def turn_on_off(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turn on and off."""
    state = hass.states.get(ENTITY_WATER_HEATER)
    expect(state.attributes.get("temperature")).to_equal(119)
    expect(state.attributes.get("away_mode")).to_equal("off")
    expect(state.attributes.get("operation_mode")).to_equal("eco")

    await common.async_turn_off(hass, ENTITY_WATER_HEATER)
    state = hass.states.get(ENTITY_WATER_HEATER)
    expect(state.attributes.get("operation_mode")).to_equal("off")

    await common.async_turn_on(hass, ENTITY_WATER_HEATER)
    state = hass.states.get(ENTITY_WATER_HEATER)
    expect(state.attributes.get("operation_mode")).to_equal("eco")
