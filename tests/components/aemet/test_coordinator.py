"""Define tests for the AEMET OpenData coordinator."""

from unittest.mock import patch

from aemet_opendata.exceptions import AemetError
from tryke import Depends, expect, fixture, test

from homeassistant.components.aemet.coordinator import WEATHER_UPDATE_INTERVAL
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant

from .util import async_init_integration

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
async def coordinator_error(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test error on coordinator update."""
    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2021-01-09 12:00:00+00:00")
    await async_init_integration(hass)

    with patch(
        "homeassistant.components.aemet.AEMET.api_call",
        side_effect=AemetError,
    ):
        freezer.tick(WEATHER_UPDATE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)

        state = hass.states.get("weather.aemet")
        expect(state.state).to_equal(STATE_UNAVAILABLE)
