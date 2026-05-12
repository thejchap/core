"""Test forecast solar energy platform."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.forecast_solar import energy
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_forecast_solar

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def energy_solar_forecast(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    forecast: MagicMock = Depends(mock_forecast_solar),
) -> None:
    """Test the Forecast.Solar energy platform solar forecast."""
    forecast.estimate.return_value.wh_period = {
        datetime(2021, 6, 27, 13, 0, tzinfo=UTC): 12,
        datetime(2021, 6, 27, 14, 0, tzinfo=UTC): 8,
    }

    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await energy.async_get_solar_forecast(hass, entry.entry_id)).to_equal(
        {
            "wh_hours": {
                "2021-06-27T13:00:00+00:00": 12,
                "2021-06-27T14:00:00+00:00": 8,
            }
        }
    )


@test
async def energy_solar_forecast_filters_midnight_utc_zeros(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    forecast: MagicMock = Depends(mock_forecast_solar),
) -> None:
    """Test that artificial zero values at UTC midnight boundaries are filtered out."""
    forecast.estimate.return_value.wh_period = {
        datetime(2021, 6, 27, 0, 0, tzinfo=UTC): 0,
        datetime(2021, 6, 27, 1, 0, tzinfo=UTC): 1388,
        datetime(2021, 6, 27, 2, 0, tzinfo=UTC): 830,
        datetime(2021, 6, 27, 14, 0, tzinfo=UTC): 0,
        datetime(2021, 6, 27, 15, 0, tzinfo=UTC): 292,
        datetime(2021, 6, 28, 0, 0, tzinfo=UTC): 0,
    }

    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    result = await energy.async_get_solar_forecast(hass, entry.entry_id)
    expect(result).to_equal(
        {
            "wh_hours": {
                "2021-06-27T01:00:00+00:00": 1388,
                "2021-06-27T02:00:00+00:00": 830,
                "2021-06-27T14:00:00+00:00": 0,
                "2021-06-27T15:00:00+00:00": 292,
            }
        }
    )


@test
async def energy_solar_forecast_invalid_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the Forecast.Solar energy platform with invalid config entry ID."""
    expect(await energy.async_get_solar_forecast(hass, "invalid_id")).to_be(None)
