"""Test the Hypontech Cloud config flow."""

from unittest.mock import AsyncMock

from hyponcloud import AuthenticationError
from tryke import Depends, expect, fixture, test

from homeassistant.components.hypontech.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_hyponcloud, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_USER_INPUT = {
    CONF_USERNAME: "test@example.com",
    CONF_PASSWORD: "test-password",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_hyponcloud),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test@example.com")
    expect(result["data"]).to_equal(TEST_USER_INPUT)
    expect(result["result"].unique_id).to_equal("2123456789123456789")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("auth_error", side_effect=AuthenticationError, error_message="invalid_auth"),
    test.case(
        "connection_error", side_effect=ConnectionError, error_message="cannot_connect"
    ),
    test.case("timeout", side_effect=TimeoutError, error_message="cannot_connect"),
    test.case("unknown", side_effect=Exception, error_message="unknown"),
)
async def form_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_hyponcloud),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    side_effect: type[Exception],
    error_message: str,
) -> None:
    """Test we handle errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    client.connect.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_message})

    client.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_hyponcloud),
) -> None:
    """Test that duplicate entries are prevented based on account ID."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_hyponcloud),
) -> None:
    """Test reauthentication flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**TEST_USER_INPUT, CONF_PASSWORD: "password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("password")


@test.cases(
    test.case("auth_error", side_effect=AuthenticationError, error_message="invalid_auth"),
    test.case(
        "connection_error", side_effect=ConnectionError, error_message="cannot_connect"
    ),
    test.case("timeout", side_effect=TimeoutError, error_message="cannot_connect"),
    test.case("unknown", side_effect=Exception, error_message="unknown"),
)
async def reauth_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_hyponcloud),
    *,
    side_effect: type[Exception],
    error_message: str,
) -> None:
    """Test reauthentication flow with errors."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    client.connect.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**TEST_USER_INPUT, CONF_PASSWORD: "new-password"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_message})

    client.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**TEST_USER_INPUT, CONF_PASSWORD: "new-password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reauth_flow_wrong_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_hyponcloud),
) -> None:
    """Test reauthentication flow with wrong account."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    client.get_admin_info.return_value.id = "different_account_id_456"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**TEST_USER_INPUT, CONF_USERNAME: "different@example.com"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_account")
