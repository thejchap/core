"""The test for the random number sensor platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def random_sensor(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the Random number sensor."""
    config = {
        "sensor": {
            "platform": "random",
            "name": "test",
            "minimum": 10,
            "maximum": 20,
        }
    }

    result = await async_setup_component(hass, "sensor", config)
    expect(result).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")
    expect(state is not None).to_be(True)
    expect(int(state.state) <= config["sensor"]["maximum"]).to_be(True)
    expect(int(state.state) >= config["sensor"]["minimum"]).to_be(True)
