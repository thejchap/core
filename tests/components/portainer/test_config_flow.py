"""Test the Portainer config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from pyportainer.exceptions import (
    PortainerAuthenticationError,
    PortainerConnectionError,
    PortainerTimeoutError,
)
from pyportainer.models.portainer import PortainerSystemStatus
from tryke import Depends, expect, fixture, test

from homeassistant.components.portainer.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_TOKEN, CONF_URL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    MOCK_TEST_CONFIG,
    mock_async_zeroconf as mock_async_zeroconf_fx,
    mock_config_entry as mock_config_entry_fx,
    mock_portainer_client as mock_portainer_client_fx,
    mock_setup_entry as mock_setup_entry_fx,
)

MOCK_USER_SETUP = {
    CONF_URL: "https://127.0.0.1:9000/",
    CONF_API_TOKEN: "test_api_token",
    CONF_VERIFY_SSL: True,
}

USER_INPUT_RECONFIGURE = {
    CONF_URL: "https://new_domain:9000/",
    CONF_API_TOKEN: "new_api_key",
    CONF_VERIFY_SSL: True,
}


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _zc: MagicMock = Depends(mock_async_zeroconf_fx),
    _client: AsyncMock = Depends(mock_portainer_client_fx),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Wire mock_network, zeroconf, portainer_client, setup_entry for every test."""


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_portainer_client: MagicMock = Depends(mock_portainer_client_fx),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_SETUP,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("https://127.0.0.1:9000/")
    expect(result["data"]).to_equal(MOCK_TEST_CONFIG)


@test.cases(
    test.case("auth", PortainerAuthenticationError, "invalid_auth"),
    test.case("connection", PortainerConnectionError, "cannot_connect"),
    test.case("timeout", PortainerTimeoutError, "timeout_connect"),
    test.case("unknown", Exception("Some other error"), "unknown"),
)
async def form_exceptions(
    exception: Exception,
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_portainer_client: AsyncMock = Depends(mock_portainer_client_fx),
) -> None:
    """Test we handle all exceptions."""
    mock_portainer_client.portainer_system_status.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_SETUP,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": reason})

    mock_portainer_client.portainer_system_status.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_SETUP,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("https://127.0.0.1:9000/")
    expect(result["data"]).to_equal(MOCK_TEST_CONFIG)


@test
async def duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test we handle duplicate entries."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_SETUP,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def full_flow_reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: MagicMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test the full flow of the config flow."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_TOKEN: "new_api_key"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_API_TOKEN]).to_equal("new_api_key")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("auth", PortainerAuthenticationError, "invalid_auth"),
    test.case("connection", PortainerConnectionError, "cannot_connect"),
    test.case("timeout", PortainerTimeoutError, "timeout_connect"),
    test.case("unknown", Exception("Some other error"), "unknown"),
)
async def reauth_flow_exceptions(
    exception: Exception,
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_portainer_client: AsyncMock = Depends(mock_portainer_client_fx),
    mock_setup_entry: MagicMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test we handle all exceptions in the reauth flow."""
    mock_config_entry.add_to_hass(hass)

    mock_portainer_client.portainer_system_status.side_effect = exception

    await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_TOKEN: "new_api_key"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": reason})

    mock_portainer_client.portainer_system_status.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_TOKEN: "new_api_key"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_API_TOKEN]).to_equal("new_api_key")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def full_flow_reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: MagicMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test the full flow of the config flow."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_RECONFIGURE,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data[CONF_API_TOKEN]).to_equal("new_api_key")
    expect(mock_config_entry.data[CONF_URL]).to_equal("https://new_domain:9000/")
    expect(mock_config_entry.data[CONF_VERIFY_SSL]).to_be(True)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def full_flow_reconfigure_unique_id_mismatch(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_portainer_client: AsyncMock = Depends(mock_portainer_client_fx),
    mock_setup_entry: MagicMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfigure aborts on different Portainer instance."""
    mock_config_entry.add_to_hass(hass)
    mock_portainer_client.portainer_system_status.return_value = PortainerSystemStatus(
        instance_id="different-instance-id", version="2.0.0"
    )
    result = await mock_config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_RECONFIGURE,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")
    expect(mock_config_entry.data[CONF_API_TOKEN]).to_equal("test_api_token")
    expect(mock_config_entry.data[CONF_URL]).to_equal("https://127.0.0.1:9000/")
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test.cases(
    test.case("auth", PortainerAuthenticationError, "invalid_auth"),
    test.case("connection", PortainerConnectionError, "cannot_connect"),
    test.case("timeout", PortainerTimeoutError, "timeout_connect"),
    test.case("unknown", Exception("Some other error"), "unknown"),
)
async def full_flow_reconfigure_exceptions(
    exception: Exception,
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_portainer_client: AsyncMock = Depends(mock_portainer_client_fx),
    mock_setup_entry: MagicMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test the reconfigure flow with exceptions."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_portainer_client.portainer_system_status.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_RECONFIGURE,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": reason})

    mock_portainer_client.portainer_system_status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_RECONFIGURE,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data[CONF_API_TOKEN]).to_equal("new_api_key")
    expect(mock_config_entry.data[CONF_URL]).to_equal("https://new_domain:9000/")
    expect(mock_config_entry.data[CONF_VERIFY_SSL]).to_be(True)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
