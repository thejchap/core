"""Test reproduce state for Automation."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.state import async_reproduce_state

from tests.common import async_mock_service
from tests.hass_fixtures import LogCapture, caplog as caplog_fixture, hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def reproducing_states(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test reproducing Automation states."""
    hass.states.async_set("automation.entity_off", "off", {})
    hass.states.async_set("automation.entity_on", "on", {})

    turn_on_calls = async_mock_service(hass, "automation", "turn_on")
    turn_off_calls = async_mock_service(hass, "automation", "turn_off")

    # These calls should do nothing as entities already in desired state
    await async_reproduce_state(
        hass,
        [State("automation.entity_off", "off"), State("automation.entity_on", "on")],
    )

    expect(len(turn_on_calls)).to_equal(0)
    expect(len(turn_off_calls)).to_equal(0)

    # Test invalid state is handled
    await async_reproduce_state(hass, [State("automation.entity_off", "not_supported")])

    expect("not_supported" in caplog.text).to_be(True)
    expect(len(turn_on_calls)).to_equal(0)
    expect(len(turn_off_calls)).to_equal(0)

    # Make sure correct services are called
    await async_reproduce_state(
        hass,
        [
            State("automation.entity_on", "off"),
            State("automation.entity_off", "on"),
            # Should not raise
            State("automation.non_existing", "on"),
        ],
    )

    expect(len(turn_on_calls)).to_equal(1)
    expect(turn_on_calls[0].domain).to_equal("automation")
    expect(turn_on_calls[0].data).to_equal({"entity_id": "automation.entity_off"})

    expect(len(turn_off_calls)).to_equal(1)
    expect(turn_off_calls[0].domain).to_equal("automation")
    expect(turn_off_calls[0].data).to_equal({"entity_id": "automation.entity_on"})
