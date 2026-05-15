"""The test for the random number sensor platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def random_sensor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the Random number sensor."""
    config = {
        "sensor": {
            "platform": "random",
            "name": "test",
            "minimum": 10,
            "maximum": 20,
        }
    }

    expect(
        bool(
            await async_setup_component(
                hass,
                "sensor",
                config,
            )
        )
    ).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")

    expect(int(state.state) <= config["sensor"]["maximum"]).to_be(True)
    expect(int(state.state) >= config["sensor"]["minimum"]).to_be(True)
