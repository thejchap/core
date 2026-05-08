"""Test init of AccuWeather integration."""

from datetime import timedelta
from unittest.mock import AsyncMock

from accuweather import ApiError, InvalidApiKeyError
from tryke import Depends, expect, fixture, test

from homeassistant.components.accuweather.const import (
    DOMAIN,
    UPDATE_INTERVAL_DAILY_FORECAST,
    UPDATE_INTERVAL_OBSERVATION,
)
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import init_integration
from ._fixtures import mock_accuweather_client

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass before tests run."""
    return hass


@test
async def async_setup_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
) -> None:
    """Test a successful setup entry."""
    await init_integration(hass)

    state = hass.states.get("weather.home")
    expect(state is not None).to_be(True)
    expect(state.state != STATE_UNAVAILABLE).to_be(True)
    expect(state.state).to_equal("sunny")


@test
async def config_not_ready(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
) -> None:
    """Test for setup failure if connection to AccuWeather is missing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Home",
        unique_id="0123456",
        data={
            "api_key": "32-character-string-1234567890qw",
            "latitude": 55.55,
            "longitude": 122.12,
            "name": "Home",
        },
    )

    mock_accuweather_client.async_get_current_conditions.side_effect = ApiError(
        "API Error"
    )

    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
) -> None:
    """Test successful unload of entry."""
    entry = await init_integration(hass)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(bool(hass.data.get(DOMAIN))).to_be(False)


@test
async def update_interval(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test correct update interval."""
    entry = await init_integration(hass)

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(mock_accuweather_client.async_get_current_conditions.call_count).to_equal(1)
    expect(mock_accuweather_client.async_get_daily_forecast.call_count).to_equal(1)

    freezer.tick(UPDATE_INTERVAL_OBSERVATION)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(mock_accuweather_client.async_get_current_conditions.call_count).to_equal(2)

    freezer.tick(UPDATE_INTERVAL_DAILY_FORECAST)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(mock_accuweather_client.async_get_daily_forecast.call_count).to_equal(2)


@test
async def remove_ozone_sensors(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
) -> None:
    """Test remove ozone sensors from registry."""
    entity_registry.async_get_or_create(
        SENSOR_DOMAIN,
        DOMAIN,
        "0123456-ozone-0",
        suggested_object_id="home_ozone_0d",
        disabled_by=None,
    )

    await init_integration(hass)

    entry = entity_registry.async_get("sensor.home_ozone_0d")
    expect(entry).to_be(None)


@test
async def auth_error(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
    mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
) -> None:
    """Test authentication error when polling data."""
    mock_accuweather_client.async_get_current_conditions.side_effect = (
        InvalidApiKeyError("Invalid API Key")
    )

    mock_config_entry = await init_integration(hass)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)

    flow = flows[0]
    expect(flow.get("step_id")).to_equal("reauth_confirm")
    expect(flow.get("handler")).to_equal(DOMAIN)

    expect("context" in flow).to_be(True)
    expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
    expect(flow["context"].get("entry_id")).to_equal(mock_config_entry.entry_id)


@test
async def auth_error_whe_polling_data(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer=Depends(freezer_fixture),
    mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
) -> None:
    """Test authentication error when polling data."""
    mock_config_entry = await init_integration(hass)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    mock_accuweather_client.async_get_current_conditions.side_effect = (
        InvalidApiKeyError("Invalid API Key")
    )
    freezer.tick(timedelta(minutes=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)

    flow = flows[0]
    expect(flow.get("step_id")).to_equal("reauth_confirm")
    expect(flow.get("handler")).to_equal(DOMAIN)

    expect("context" in flow).to_be(True)
    expect(flow["context"].get("source")).to_equal(SOURCE_REAUTH)
    expect(flow["context"].get("entry_id")).to_equal(mock_config_entry.entry_id)
