"""The test for the Random binary sensor platform."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def random_binary_sensor_on(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the Random binary sensor."""
    config = {"binary_sensor": {"platform": "random", "name": "test"}}

    with patch(
        "homeassistant.components.random.binary_sensor.getrandbits",
        return_value=1,
    ):
        result = await async_setup_component(hass, "binary_sensor", config)
        expect(result).to_be(True)
        await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test")

    expect(state is not None).to_be(True)
    expect(state.state).to_equal("on")


@test
async def random_binary_sensor_off(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the Random binary sensor."""
    config = {"binary_sensor": {"platform": "random", "name": "test"}}

    with patch(
        "homeassistant.components.random.binary_sensor.getrandbits",
        return_value=False,
    ):
        result = await async_setup_component(hass, "binary_sensor", config)
        expect(result).to_be(True)
        await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test")

    expect(state is not None).to_be(True)
    expect(state.state).to_equal("off")
