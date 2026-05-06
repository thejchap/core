"""The image tests for the AEMET OpenData platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from .util import async_init_integration

from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
async def aemet_create_images(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test creation of AEMET images."""
    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2021-01-09 12:00:00+00:00")
    await async_init_integration(hass)

    state = hass.states.get("image.aemet_weather_radar")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal("2021-01-09T11:34:06.448809+00:00")
