"""Test the Roth Touchline SL config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test
from pytouchlinesl.client import RothAPIError

from homeassistant.components.touchline_sl.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_setup_entry, mock_touchlinesl_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

RESULT_UNIQUE_ID = "12345"

CONFIG_DATA = {
    CONF_USERNAME: "test-username",
    CONF_PASSWORD: "test-password",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def config_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _touchlinesl: AsyncMock = Depends(mock_touchlinesl_client),
) -> None:
    """Test the happy path where the provided username/password result in a new entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_DATA
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test-username")
    expect(result["data"]).to_equal(CONFIG_DATA)
    expect(result["result"].unique_id).to_equal(RESULT_UNIQUE_ID)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", exception=RothAPIError(status=401), error_base="invalid_auth"),
    test.case("cannot_connect", exception=RothAPIError(status=502), error_base="cannot_connect"),
    test.case("unknown", exception=Exception, error_base="unknown"),
)
async def config_flow_failure_api_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    touchlinesl: AsyncMock = Depends(mock_touchlinesl_client),
    *,
    exception: Exception,
    error_base: str,
) -> None:
    """Test for invalid credentials or API connection errors, and that the form can recover."""
    touchlinesl.user_id.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_DATA
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_base})

    # "Fix" the problem, and try again.
    touchlinesl.user_id.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_DATA
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test-username")
    expect(result["data"]).to_equal(CONFIG_DATA)
    expect(result["result"].unique_id).to_equal(RESULT_UNIQUE_ID)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def config_flow_failure_adding_non_unique_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _touchlinesl: AsyncMock = Depends(mock_touchlinesl_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that the config flow fails when user tries to add duplicate accounts."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONFIG_DATA
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
