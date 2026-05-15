"""Test reproduce state for input boolean."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.state import async_reproduce_state
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def reproducing_states(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test reproducing input_boolean states."""
    expect(
        await async_setup_component(
            hass,
            "input_boolean",
            {
                "input_boolean": {
                    "initial_on": {"initial": True},
                    "initial_off": {"initial": False},
                }
            },
        )
    ).to_be_truthy()
    await async_reproduce_state(
        hass,
        [
            State("input_boolean.initial_on", "off"),
            State("input_boolean.initial_off", "on"),
            # Should not raise
            State("input_boolean.non_existing", "on"),
        ],
    )
    expect(hass.states.get("input_boolean.initial_off").state).to_equal("on")
    expect(hass.states.get("input_boolean.initial_on").state).to_equal("off")

    await async_reproduce_state(
        hass,
        [
            # Test invalid state
            State("input_boolean.initial_on", "invalid_state"),
            # Set to state it already is.
            State("input_boolean.initial_off", "on"),
        ],
    )

    expect(hass.states.get("input_boolean.initial_on").state).to_equal("off")
    expect(hass.states.get("input_boolean.initial_off").state).to_equal("on")
