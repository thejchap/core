"""Test the Uhoo config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test
from uhooapi.errors import ForbiddenError, UhooError, UnauthorizedError

from homeassistant.components.uhoo.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_setup_entry, mock_uhoo_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_uhoo_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a complete user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "valid-api-key-12345"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("uHoo (12345)")
    expect(result["data"]).to_equal({CONF_API_KEY: "valid-api-key-12345"})

    setup_entry.assert_called_once()


@test
async def user_duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate entry aborts."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "valid-api-key-12345"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "uhoo_error", exception=UhooError("asd"), error_type="cannot_connect"
    ),
    test.case(
        "unauthorized",
        exception=UnauthorizedError("Invalid credentials"),
        error_type="invalid_auth",
    ),
    test.case(
        "forbidden",
        exception=ForbiddenError("Forbidden"),
        error_type="invalid_auth",
    ),
    test.case("unknown", exception=Exception(), error_type="unknown"),
)
async def user_flow_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_uhoo_client),
    *,
    exception: Exception,
    error_type: str,
) -> None:
    """Test form when client raises various exceptions."""
    client.login.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_equal(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "test-api-key"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error_type})

    client.login.assert_called_once()
    client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "test-api-key"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_uhoo_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauthentication flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new-api-key-67890"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_API_KEY]).to_equal("new-api-key-67890")


@test.cases(
    test.case(
        "unauthorized",
        exception=UnauthorizedError("Invalid credentials"),
        error_type="invalid_auth",
    ),
    test.case(
        "forbidden",
        exception=ForbiddenError("Forbidden"),
        error_type="invalid_auth",
    ),
    test.case(
        "uhoo_error", exception=UhooError("asd"), error_type="cannot_connect"
    ),
    test.case("unknown", exception=Exception(), error_type="unknown"),
)
async def reauth_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_uhoo_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: Exception,
    error_type: str,
) -> None:
    """Test reauthentication flow with errors and recovery."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    client.login.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new-api-key-67890"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": error_type})

    client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new-api-key-67890"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_API_KEY]).to_equal("new-api-key-67890")
