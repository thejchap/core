"""Tests for the Forecast.Solar integration."""

from unittest.mock import MagicMock, patch

from forecast_solar import ForecastSolarConnectionError, Plane
from tryke import Depends, expect, fixture, test

from homeassistant.components.forecast_solar.const import (
    CONF_AZIMUTH,
    CONF_DAMPING,
    CONF_DAMPING_EVENING,
    CONF_DAMPING_MORNING,
    CONF_DECLINATION,
    CONF_INVERTER_SIZE,
    CONF_MODULES_POWER,
    DOMAIN,
    SUBENTRY_TYPE_PLANE,
)
from homeassistant.config_entries import ConfigEntryState, ConfigSubentryData
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import mock_config_entry, mock_forecast_solar

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def load_unload_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_forecast_solar: MagicMock = Depends(mock_forecast_solar),
) -> None:
    """Test the Forecast.Solar configuration entry loading/unloading."""
    mock_config_entry.add_to_hass(hass)
    await async_setup_component(hass, "forecast_solar", {})

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(hass.data.get(DOMAIN)).to_be(None)


@test
async def config_entry_not_ready(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the Forecast.Solar configuration entry not ready."""
    with patch(
        "homeassistant.components.forecast_solar.coordinator.ForecastSolar.estimate",
        side_effect=ForecastSolarConnectionError,
    ) as mock_request:
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        expect(mock_request.call_count).to_equal(1)
        expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def migration_from_v1(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_forecast_solar: MagicMock = Depends(mock_forecast_solar),
) -> None:
    """Test config entry migration from version 1."""
    mock_config_entry = MockConfigEntry(
        title="Green House",
        unique_id="unique",
        domain=DOMAIN,
        version=1,
        data={
            CONF_LATITUDE: 52.42,
            CONF_LONGITUDE: 4.42,
        },
        options={
            CONF_API_KEY: "abcdef12345",
            CONF_DECLINATION: 30,
            CONF_AZIMUTH: 190,
            "modules power": 5100,
            CONF_DAMPING: 0.5,
            CONF_INVERTER_SIZE: 2000,
        },
    )
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entry = hass.config_entries.async_get_entry(mock_config_entry.entry_id)
    expect(entry.version).to_equal(3)
    expect(entry.options).to_equal(
        {
            CONF_API_KEY: "abcdef12345",
            "damping_morning": 0.5,
            "damping_evening": 0.5,
            CONF_INVERTER_SIZE: 2000,
        }
    )
    plane_subentries = entry.get_subentries_of_type(SUBENTRY_TYPE_PLANE)
    expect(len(plane_subentries)).to_equal(1)
    subentry = plane_subentries[0]
    expect(subentry.subentry_type).to_equal(SUBENTRY_TYPE_PLANE)
    expect(subentry.data).to_equal(
        {
            CONF_DECLINATION: 30,
            CONF_AZIMUTH: 190,
            CONF_MODULES_POWER: 5100,
        }
    )
    expect(subentry.title).to_equal("30° / 190° / 5100W")


@test
async def migration_from_v2(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_forecast_solar: MagicMock = Depends(mock_forecast_solar),
) -> None:
    """Test config entry migration from version 2."""
    mock_config_entry = MockConfigEntry(
        title="Green House",
        unique_id="unique",
        domain=DOMAIN,
        version=2,
        data={
            CONF_LATITUDE: 52.42,
            CONF_LONGITUDE: 4.42,
        },
        options={
            CONF_API_KEY: "abcdef12345",
            CONF_DECLINATION: 30,
            CONF_AZIMUTH: 190,
            CONF_MODULES_POWER: 5100,
            CONF_INVERTER_SIZE: 2000,
        },
    )
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entry = hass.config_entries.async_get_entry(mock_config_entry.entry_id)
    expect(entry.version).to_equal(3)
    expect(entry.options).to_equal(
        {
            CONF_API_KEY: "abcdef12345",
            CONF_INVERTER_SIZE: 2000,
        }
    )
    plane_subentries = entry.get_subentries_of_type(SUBENTRY_TYPE_PLANE)
    expect(len(plane_subentries)).to_equal(1)
    subentry = plane_subentries[0]
    expect(subentry.subentry_type).to_equal(SUBENTRY_TYPE_PLANE)
    expect(subentry.data).to_equal(
        {
            CONF_DECLINATION: 30,
            CONF_AZIMUTH: 190,
            CONF_MODULES_POWER: 5100,
        }
    )
    expect(subentry.title).to_equal("30° / 190° / 5100W")


@test
async def setup_entry_no_planes(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_forecast_solar: MagicMock = Depends(mock_forecast_solar),
) -> None:
    """Test setup fails when all plane subentries have been removed."""
    mock_config_entry = MockConfigEntry(
        title="Green House",
        unique_id="unique",
        version=3,
        domain=DOMAIN,
        data={
            CONF_LATITUDE: 52.42,
            CONF_LONGITUDE: 4.42,
        },
        options={
            CONF_API_KEY: "abcdef1234567890",
        },
    )
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def setup_entry_multiple_planes_no_api_key(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_forecast_solar: MagicMock = Depends(mock_forecast_solar),
) -> None:
    """Test setup fails when multiple planes are configured without an API key."""
    mock_config_entry = MockConfigEntry(
        title="Green House",
        unique_id="unique",
        version=3,
        domain=DOMAIN,
        data={
            CONF_LATITUDE: 52.42,
            CONF_LONGITUDE: 4.42,
        },
        options={},
        subentries_data=[
            ConfigSubentryData(
                data={
                    CONF_DECLINATION: 30,
                    CONF_AZIMUTH: 190,
                    CONF_MODULES_POWER: 5100,
                },
                subentry_id="plane_1",
                subentry_type=SUBENTRY_TYPE_PLANE,
                title="30° / 190° / 5100W",
                unique_id=None,
            ),
            ConfigSubentryData(
                data={
                    CONF_DECLINATION: 45,
                    CONF_AZIMUTH: 90,
                    CONF_MODULES_POWER: 3000,
                },
                subentry_id="plane_2",
                subentry_type=SUBENTRY_TYPE_PLANE,
                title="45° / 90° / 3000W",
                unique_id=None,
            ),
        ],
    )
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def coordinator_multi_plane_initialization(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_forecast_solar: MagicMock = Depends(mock_forecast_solar),
) -> None:
    """Test the Forecast.Solar coordinator multi-plane initialization."""
    options = {
        CONF_API_KEY: "abcdef1234567890",
        CONF_DAMPING_MORNING: 0.5,
        CONF_DAMPING_EVENING: 0.5,
        CONF_INVERTER_SIZE: 2000,
    }

    mock_config_entry = MockConfigEntry(
        title="Green House",
        unique_id="unique",
        version=3,
        domain=DOMAIN,
        data={
            CONF_LATITUDE: 52.42,
            CONF_LONGITUDE: 4.42,
        },
        options=options,
        subentries_data=[
            ConfigSubentryData(
                data={
                    CONF_DECLINATION: 30,
                    CONF_AZIMUTH: 190,
                    CONF_MODULES_POWER: 5100,
                },
                subentry_id="plane_1",
                subentry_type=SUBENTRY_TYPE_PLANE,
                title="30° / 190° / 5100W",
                unique_id=None,
            ),
            ConfigSubentryData(
                data={
                    CONF_DECLINATION: 45,
                    CONF_AZIMUTH: 270,
                    CONF_MODULES_POWER: 3000,
                },
                subentry_id="plane_2",
                subentry_type=SUBENTRY_TYPE_PLANE,
                title="45° / 270° / 3000W",
                unique_id=None,
            ),
        ],
    )

    mock_config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.forecast_solar.coordinator.ForecastSolar",
        return_value=mock_forecast_solar,
    ) as forecast_solar_mock:
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    forecast_solar_mock.assert_called_once()
    _, kwargs = forecast_solar_mock.call_args

    expect(kwargs["latitude"]).to_equal(52.42)
    expect(kwargs["longitude"]).to_equal(4.42)
    expect(kwargs["api_key"]).to_equal("abcdef1234567890")

    expect(kwargs["declination"]).to_equal(30)
    expect(kwargs["azimuth"]).to_equal(10)
    expect(kwargs["kwp"]).to_equal(5.1)

    planes = kwargs["planes"]
    expect(len(planes)).to_equal(1)
    expect(isinstance(planes[0], Plane)).to_be(True)
    expect(planes[0].declination).to_equal(45)
    expect(planes[0].azimuth).to_equal(90)
    expect(planes[0].kwp).to_equal(3.0)
