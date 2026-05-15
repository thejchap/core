"""Tryke fixtures for flux switch tests."""

from tryke import Depends, fixture

from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant

from tests.components.light.common import MockLight
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def set_utc(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set timezone to UTC."""
    await hass.config.async_set_time_zone("UTC")


@fixture
def mock_light_entities() -> list[MockLight]:
    """Return mocked light entities."""
    return [
        MockLight("Ceiling", STATE_ON),
        MockLight("Ceiling", STATE_OFF),
        MockLight(None, STATE_OFF),
    ]
