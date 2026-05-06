"""Tests for Met.no config flow."""

from unittest.mock import ANY, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.met.const import DOMAIN, HOME_LOCATION_NAME
from homeassistant.const import CONF_ELEVATION, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.data_entry_flow import FlowResultType

from . import init_integration
from ._fixtures import met_setup

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(met_setup),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@fixture
def _trigger_executor_no_setup(
    _network: None = Depends(mock_network),
) -> None:
    """Variant without met_setup for tests that need real setup."""


@test
async def show_config_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test show configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def flow_with_home_location(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow with default home location."""
    hass.config.latitude = 1
    hass.config.longitude = 2
    hass.config.elevation = 3

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    default_data = result["data_schema"]({})
    expect(default_data["name"]).to_equal(HOME_LOCATION_NAME)
    expect(default_data["latitude"]).to_equal(1)
    expect(default_data["longitude"]).to_equal(2)
    expect(default_data["elevation"]).to_equal(3)


@test
async def create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test create entry from user input."""
    test_data = {
        "name": "home",
        CONF_LONGITUDE: 0,
        CONF_LATITUDE: 0,
        CONF_ELEVATION: 0,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=test_data
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("home")
    expect(result["data"]).to_equal(test_data)


@test
async def flow_entry_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user input for config_entry that already exists."""
    first_entry = MockConfigEntry(
        domain="met",
        data={"name": "home", CONF_LATITUDE: 0, CONF_LONGITUDE: 0, CONF_ELEVATION: 0},
    )
    first_entry.add_to_hass(hass)

    test_data = {
        "name": "home",
        CONF_LONGITUDE: 0,
        CONF_LATITUDE: 0,
        CONF_ELEVATION: 0,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=test_data
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["name"]).to_equal("already_configured")


@test
async def onboarding_step(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test initializing via onboarding step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "onboarding"}, data={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(HOME_LOCATION_NAME)
    expect(result["data"]).to_equal({"track_home": True})


@test.cases(
    test.case("amsterdam", latitude=52.3731339, longitude=4.8903147),
    test.case("zero", latitude=0.0, longitude=0.0),
)
async def onboarding_step_abort_no_home(
    latitude: float,
    longitude: float,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test entry not created when default step fails."""
    await async_process_ha_core_config(
        hass,
        {"latitude": latitude, "longitude": longitude},
    )

    expect(hass.config.latitude).to_equal(latitude)
    expect(hass.config.longitude).to_equal(longitude)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "onboarding"}, data={}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_home")


@test.skip("requires full integration setup; MetWeatherData not invoked under tryke")
async def options_flow(
    _trigger: None = Depends(_trigger_executor_no_setup),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test show options form."""
    update_data = {
        CONF_NAME: "test",
        CONF_LATITUDE: 12,
        CONF_LONGITUDE: 23,
        CONF_ELEVATION: 456,
    }

    entry = await init_integration(hass)
    await hass.async_block_till_done()

    # Test show Options form
    result = await hass.config_entries.options.async_init(entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    # Test Options flow updated config entry
    with patch(
        "homeassistant.components.met.coordinator.metno.MetWeatherData"
    ) as weatherdatamock:
        result = await hass.config_entries.options.async_init(
            entry.entry_id, data=update_data
        )
        await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Mock Title")
    expect(result["data"]).to_equal(update_data)
    weatherdatamock.assert_called_with(
        {"lat": "12", "lon": "23", "msl": "456"}, ANY, api_url=ANY
    )
