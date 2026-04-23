"""Tests for Met Éireann config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.met_eireann.const import DOMAIN, HOME_LOCATION_NAME
from homeassistant.const import CONF_ELEVATION, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import met_eireann_setup

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mes: None = Depends(met_eireann_setup),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def show_config_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test show configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)


@test
async def flow_with_home_location(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test config flow with default location configured."""
    hass.config.latitude = 1
    hass.config.longitude = 2
    hass.config.elevation = 3

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

    default_data = result["data_schema"]({})
    expect(default_data["name"]).to_equal(HOME_LOCATION_NAME)
    expect(default_data["latitude"]).to_equal(1)
    expect(default_data["longitude"]).to_equal(2)
    expect(default_data["elevation"]).to_equal(3)


@test
async def create_entry(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test create entry from user input."""
    test_data = {
        "name": "test",
        CONF_LONGITUDE: 0,
        CONF_LATITUDE: 0,
        CONF_ELEVATION: 0,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=test_data
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(test_data.get("name"))
    expect(result["data"]).to_equal(test_data)


@test
async def flow_entry_already_exists(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user input for config_entry that already exists."""
    test_data = {
        "name": "test",
        CONF_LONGITUDE: 0,
        CONF_LATITUDE: 0,
        CONF_ELEVATION: 0,
    }

    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=test_data
    )
    expect(result1["type"]).to_be(FlowResultType.CREATE_ENTRY)

    result2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=test_data
    )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")
