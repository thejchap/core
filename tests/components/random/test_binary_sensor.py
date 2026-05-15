"""The test for the Random binary sensor platform."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def random_binary_sensor_on(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the Random binary sensor."""
    config = {"binary_sensor": {"platform": "random", "name": "test"}}

    with patch(
        "homeassistant.components.random.binary_sensor.getrandbits",
        return_value=1,
    ):
        expect(bool(await async_setup_component(hass, "binary_sensor", config))).to_be(
            True
        )
        await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test")
    expect(state.state).to_equal("on")


@test
async def random_binary_sensor_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the Random binary sensor."""
    config = {"binary_sensor": {"platform": "random", "name": "test"}}

    with patch(
        "homeassistant.components.random.binary_sensor.getrandbits",
        return_value=False,
    ):
        expect(bool(await async_setup_component(hass, "binary_sensor", config))).to_be(
            True
        )
        await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test")
    expect(state.state).to_equal("off")
