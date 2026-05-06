"""Tests for the IRM KMI config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.irm_kmi.const import CONF_LANGUAGE_OVERRIDE, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    CONF_LOCATION,
    CONF_UNIQUE_ID,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_config_entry,
    mock_get_forecast_api_error,
    mock_get_forecast_in_benelux,
    mock_get_forecast_out_benelux_then_in_belgium,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _forecast: None = Depends(mock_get_forecast_in_benelux),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LOCATION: {ATTR_LATITUDE: 50.123, ATTR_LONGITUDE: 4.456}},
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal("Brussels")
    expect(result.get("data")).to_equal(
        {
            CONF_LOCATION: {ATTR_LATITUDE: 50.123, ATTR_LONGITUDE: 4.456},
            CONF_UNIQUE_ID: "brussels be",
        }
    )


@test
async def user_flow_home(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _forecast: None = Depends(mock_get_forecast_in_benelux),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LOCATION: {ATTR_LATITUDE: 50.123, ATTR_LONGITUDE: 4.456}},
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal("Brussels")


@test
async def config_flow_location_out_benelux(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _forecast: None = Depends(mock_get_forecast_out_benelux_then_in_belgium),
) -> None:
    """Test configuration flow with a zone outside of Benelux."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LOCATION: {ATTR_LATITUDE: 0.123, ATTR_LONGITUDE: 0.456}},
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(CONF_LOCATION in result.get("errors")).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LOCATION: {ATTR_LATITUDE: 50.123, ATTR_LONGITUDE: 4.456}},
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)


@test
async def config_flow_with_api_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _forecast: None = Depends(mock_get_forecast_api_error),
) -> None:
    """Test when API returns an error during the configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LOCATION: {ATTR_LATITUDE: 50.123, ATTR_LONGITUDE: 4.456}},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)


@test
async def setup_twice_same_location(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _forecast: None = Depends(mock_get_forecast_in_benelux),
) -> None:
    """Test when the user tries to set up the weather twice for the same location."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LOCATION: {ATTR_LATITUDE: 50.5, ATTR_LONGITUDE: 4.6}},
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)

    # Set up a second time
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LOCATION: {ATTR_LATITUDE: 50.5, ATTR_LONGITUDE: 4.6}},
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)


@test
async def option_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test when the user changes options with the option flow."""
    config_entry.add_to_hass(hass)

    expect(bool(config_entry.options)).to_be(False)

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, data=None
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_LANGUAGE_OVERRIDE: "none"})
