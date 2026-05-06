"""The sensor tests for the AEMET OpenData platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.weather import ATTR_CONDITION_SNOWY
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

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
async def aemet_forecast_create_sensors(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test creation of forecast sensors."""
    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2021-01-09 12:00:00+00:00")
    await async_init_integration(hass)

    state = hass.states.get("sensor.aemet_daily_forecast_condition")
    expect(state.state).to_equal(ATTR_CONDITION_SNOWY)

    state = hass.states.get("sensor.aemet_daily_forecast_precipitation_probability")
    expect(state.state).to_equal("0")

    state = hass.states.get("sensor.aemet_daily_forecast_temperature")
    expect(state.state).to_equal("2")

    state = hass.states.get("sensor.aemet_daily_forecast_temperature_low")
    expect(state.state).to_equal("-1")

    state = hass.states.get("sensor.aemet_daily_forecast_time")
    expect(state.state).to_equal(
        dt_util.parse_datetime("2021-01-08 23:00:00+00:00").isoformat()
    )

    state = hass.states.get("sensor.aemet_daily_forecast_wind_bearing")
    expect(state.state).to_equal("90.0")

    state = hass.states.get("sensor.aemet_daily_forecast_wind_speed")
    expect(state.state).to_equal("0")

    for entity_id in (
        "sensor.aemet_hourly_forecast_condition",
        "sensor.aemet_hourly_forecast_precipitation",
        "sensor.aemet_hourly_forecast_precipitation_probability",
        "sensor.aemet_hourly_forecast_temperature",
        "sensor.aemet_hourly_forecast_temperature_low",
        "sensor.aemet_hourly_forecast_time",
        "sensor.aemet_hourly_forecast_wind_bearing",
        "sensor.aemet_hourly_forecast_wind_max_speed",
        "sensor.aemet_hourly_forecast_wind_speed",
    ):
        expect(hass.states.get(entity_id)).to_be(None)


@test
async def aemet_weather_create_sensors(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test creation of weather sensors."""
    await hass.config.async_set_time_zone("UTC")
    freezer.move_to("2021-01-09 12:00:00+00:00")
    await async_init_integration(hass)

    expected = {
        "sensor.aemet_condition": ATTR_CONDITION_SNOWY,
        "sensor.aemet_humidity": "99.0",
        "sensor.aemet_pressure": "1004.4",
        "sensor.aemet_rain": "7.0",
        "sensor.aemet_rain_probability": "100",
        "sensor.aemet_snow": "1.2",
        "sensor.aemet_snow_probability": "100",
        "sensor.aemet_station_id": "3195",
        "sensor.aemet_station_name": "MADRID RETIRO",
        "sensor.aemet_station_timestamp": "2021-01-09T12:00:00+00:00",
        "sensor.aemet_storm_probability": "0",
        "sensor.aemet_temperature": "-0.7",
        "sensor.aemet_temperature_feeling": "-4",
        "sensor.aemet_town_id": "id28065",
        "sensor.aemet_town_name": "Getafe",
        "sensor.aemet_town_timestamp": "2021-01-09T11:47:45+00:00",
        "sensor.aemet_wind_bearing": "122.0",
        "sensor.aemet_wind_max_speed": "12.2",
        "sensor.aemet_wind_speed": "3.2",
    }
    for entity_id, value in expected.items():
        state = hass.states.get(entity_id)
        expect(state.state).to_equal(value)
