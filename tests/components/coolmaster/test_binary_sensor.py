"""The test for the Coolmaster binary sensor platform."""

from tryke import Depends, expect, fixture, test

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
async def binary_sensor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster binary sensor."""
    expect(hass.states.get("binary_sensor.l1_100_clean_filter").state).to_equal("off")
    expect(hass.states.get("binary_sensor.l1_101_clean_filter").state).to_equal("on")


_ = (load_int, reset_warned_fan_speeds)
