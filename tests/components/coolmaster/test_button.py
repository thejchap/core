"""The test for the Coolmaster button platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from ._fixtures import load_int, reset_warned_fan_speeds

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def button(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster button."""
    expect(hass.states.get("binary_sensor.l1_101_clean_filter").state).to_equal("on")

    button_state = hass.states.get("button.l1_101_reset_filter")
    expect(button_state is not None).to_be(True)
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {
            ATTR_ENTITY_ID: button_state.entity_id,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    expect(hass.states.get("binary_sensor.l1_101_clean_filter").state).to_equal("off")


_ = (load_int, reset_warned_fan_speeds)
