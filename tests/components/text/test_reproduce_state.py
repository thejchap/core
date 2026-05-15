"""Test reproduce state for Text entities."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.text.const import (
    ATTR_MAX,
    ATTR_MIN,
    ATTR_MODE,
    ATTR_PATTERN,
    DOMAIN,
    SERVICE_SET_VALUE,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.state import async_reproduce_state

from tests.common import async_mock_service
from tests.hass_fixtures import LogCapture, caplog as caplog_fixture, hass as hass_fixture

VALID_TEXT1 = "Hello"
VALID_TEXT2 = "World"


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
    """Test reproducing Text states."""

    hass.states.async_set(
        "text.test_text",
        VALID_TEXT1,
        {ATTR_MIN: 1, ATTR_MAX: 5, ATTR_MODE: "text", ATTR_PATTERN: None},
    )

    # These calls should do nothing as entities already in desired state
    await async_reproduce_state(
        hass,
        [
            State("text.test_text", VALID_TEXT1),
            # Should not raise
            State("text.non_existing", "234"),
        ],
    )

    expect(hass.states.get("text.test_text").state).to_equal(VALID_TEXT1)

    # Test reproducing with different state
    calls = async_mock_service(hass, DOMAIN, SERVICE_SET_VALUE)
    await async_reproduce_state(
        hass,
        [
            State("text.test_text", VALID_TEXT2),
            # Should not raise
            State("text.non_existing", "234"),
        ],
    )

    expect(len(calls)).to_equal(1)
    expect(calls[0].domain).to_equal(DOMAIN)
    expect(calls[0].data).to_equal({"entity_id": "text.test_text", "value": VALID_TEXT2})
