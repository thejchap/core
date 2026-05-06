"""The weather tests for the AEMET OpenData platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.aemet.const import ATTRIBUTION
from homeassistant.components.weather import (
    ATTR_CONDITION_SNOWY,
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_GUST_SPEED,
    ATTR_WEATHER_WIND_SPEED,
)
from homeassistant.const import ATTR_ATTRIBUTION
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
async def aemet_weather(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test states of the weather."""
    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2021-01-09 12:00:00+00:00")
    await async_init_integration(hass)

    state = hass.states.get("weather.aemet")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(ATTR_CONDITION_SNOWY)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(ATTRIBUTION)
    expect(state.attributes[ATTR_WEATHER_HUMIDITY]).to_equal(99.0)
    expect(state.attributes[ATTR_WEATHER_PRESSURE]).to_equal(1004.4)
    expect(state.attributes[ATTR_WEATHER_TEMPERATURE]).to_equal(-0.7)
    expect(state.attributes[ATTR_WEATHER_WIND_BEARING]).to_equal(122.0)
    expect(state.attributes[ATTR_WEATHER_WIND_GUST_SPEED]).to_equal(12.2)
    expect(state.attributes[ATTR_WEATHER_WIND_SPEED]).to_equal(3.2)

    expect(hass.states.get("weather.aemet_hourly")).to_be(None)


@test.skip("uses syrupy snapshot")
async def forecast_service() -> None:
    """Test multiple forecast (snapshot)."""


@test.skip("uses syrupy snapshot and hass_ws_client")
async def forecast_subscription() -> None:
    """Test forecast WS subscription (snapshot)."""
