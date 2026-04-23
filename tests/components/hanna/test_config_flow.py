"""Tests for the Hanna Instruments integration config flow."""

from unittest.mock import MagicMock

from hanna_cloud import AuthenticationError
from requests.exceptions import ConnectionError as RequestsConnectionError, Timeout
from tryke import Depends, expect, fixture, test

from homeassistant.components.hanna.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.hanna._fixtures import (
    mock_config_entry,
    mock_hanna_client,
    mock_setup_entry,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: None = Depends(mock_setup_entry),
    _mock_hanna_client: MagicMock = Depends(mock_hanna_client),
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        },
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("test@example.com")
    expect(result["data"]).to_equal(
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        }
    )
    expect(result["result"].unique_id).to_equal("test@example.com")


@test.cases(
    test.case(
        "auth_error",
        AuthenticationError("Authentication failed"),
        "invalid_auth",
    ),
    test.case(
        "timeout",
        Timeout("Connection timeout"),
        "cannot_connect",
    ),
    test.case(
        "connection_error",
        RequestsConnectionError("Connection failed"),
        "cannot_connect",
    ),
)
async def error_scenarios(
    exception: Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: None = Depends(mock_setup_entry),
    mock_hanna_client: MagicMock = Depends(mock_hanna_client),
) -> None:
    """Test various error scenarios in the config flow."""
    mock_hanna_client.authenticate.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": expected_error})

    mock_hanna_client.authenticate.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("test@example.com")
    expect(result["data"]).to_equal(
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        }
    )


@test
async def duplicate_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: None = Depends(mock_setup_entry),
    _mock_hanna_client: MagicMock = Depends(mock_hanna_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that duplicate entries are aborted."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
