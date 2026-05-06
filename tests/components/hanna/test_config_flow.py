"""Tests for the Hanna Instruments integration config flow."""

from unittest.mock import AsyncMock, MagicMock

from hanna_cloud import AuthenticationError
from requests.exceptions import ConnectionError as RequestsConnectionError, Timeout
from tryke import Depends, expect, fixture, test

from homeassistant.components.hanna.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_hanna_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hanna_client: MagicMock = Depends(mock_hanna_client),
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
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
        "auth",
        exception=AuthenticationError("Authentication failed"),
        expected_error="invalid_auth",
    ),
    test.case(
        "timeout",
        exception=Timeout("Connection timeout"),
        expected_error="cannot_connect",
    ),
    test.case(
        "connection",
        exception=RequestsConnectionError("Connection failed"),
        expected_error="cannot_connect",
    ),
)
async def error_scenarios(
    exception: Exception,
    expected_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hanna_client: MagicMock = Depends(mock_hanna_client),
) -> None:
    """Test various error scenarios in the config flow."""
    hanna_client.authenticate.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": expected_error})

    # Repatch to succeed and complete the flow
    hanna_client.authenticate.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test@example.com")
    expect(result["data"]).to_equal(
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        }
    )


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hanna_client: MagicMock = Depends(mock_hanna_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that duplicate entries are aborted."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_EMAIL: "test@example.com", CONF_PASSWORD: "test-password"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
