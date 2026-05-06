"""Define tests for the GIOS config flow."""

from unittest.mock import MagicMock

from gios import ApiError, InvalidSensorsDataError
from tryke import Depends, expect, fixture, test

from homeassistant.components.gios.const import CONF_STATION_ID, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_gios

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

CONFIG = {
    CONF_STATION_ID: "123",
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _gios: MagicMock = Depends(mock_gios),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def happy_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(len(result["data_schema"].schema[CONF_STATION_ID].config["options"])).to_equal(2)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Home")
    expect(result["data"]).to_equal(
        {
            CONF_STATION_ID: 123,
            CONF_NAME: "Home",
        }
    )

    expect(result["result"].unique_id).to_equal("123")


@test
async def form_with_api_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    gios: MagicMock = Depends(mock_gios),
) -> None:
    """Test the form is aborted because of API error."""
    gios.create.side_effect = ApiError("error")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test.cases(
    test.case(
        "invalid_sensors_data",
        exception=InvalidSensorsDataError("Invalid data"),
        errors={CONF_STATION_ID: "invalid_sensors_data"},
    ),
    test.case(
        "api_error",
        exception=ApiError("error"),
        errors={"base": "cannot_connect"},
    ),
)
async def form_submission_errors(
    exception: Exception,
    errors: dict,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    gios: MagicMock = Depends(mock_gios),
) -> None:
    """Test errors during form submission."""
    gios.async_update.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(errors)

    gios.async_update.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=CONFIG
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Home")


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that duplicate station IDs are rejected."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
