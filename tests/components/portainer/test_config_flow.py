"""Test the Portainer config flow."""

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

from ._fixtures import (
    MOCK_TEST_CONFIG,
    mock_config_entry,
    mock_portainer_client,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

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
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_portainer_client),
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
    test.case("auth_error", exception=PortainerAuthenticationError, reason="invalid_auth"),
    test.case("connection_error", exception=PortainerConnectionError, reason="cannot_connect"),
    test.case("timeout_error", exception=PortainerTimeoutError, reason="timeout_connect"),
    test.case("other_exception", exception=Exception("Some other error"), reason="unknown"),
)
async def form_exceptions(
    exception: Exception,
    reason: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_portainer_client),
) -> None:
    """Test we handle all exceptions."""
    client.portainer_system_status.side_effect = exception

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

    client.portainer_system_status.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_SETUP,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("https://127.0.0.1:9000/")
    expect(result["data"]).to_equal(MOCK_TEST_CONFIG)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_portainer_client),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we handle duplicate entries."""
    config_entry.add_to_hass(hass)

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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_portainer_client),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the full flow of the reauth flow."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await config_entry.start_reauth_flow(hass)
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
    expect(config_entry.data[CONF_API_TOKEN]).to_equal("new_api_key")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("auth_error", exception=PortainerAuthenticationError, reason="invalid_auth"),
    test.case("connection_error", exception=PortainerConnectionError, reason="cannot_connect"),
    test.case("timeout_error", exception=PortainerTimeoutError, reason="timeout_connect"),
    test.case("other_exception", exception=Exception("Some other error"), reason="unknown"),
)
async def reauth_flow_exceptions(
    exception: Exception,
    reason: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_portainer_client),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we handle all exceptions in the reauth flow."""
    config_entry.add_to_hass(hass)

    client.portainer_system_status.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_TOKEN: "new_api_key"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": reason})

    client.portainer_system_status.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_TOKEN: "new_api_key"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_API_TOKEN]).to_equal("new_api_key")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def full_flow_reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_portainer_client),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the full reconfigure flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_RECONFIGURE,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_API_TOKEN]).to_equal("new_api_key")
    expect(config_entry.data[CONF_URL]).to_equal("https://new_domain:9000/")
    expect(config_entry.data[CONF_VERIFY_SSL]).to_be(True)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def full_flow_reconfigure_unique_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_portainer_client),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure aborts when credentials point to a different Portainer instance."""
    config_entry.add_to_hass(hass)
    client.portainer_system_status.return_value = PortainerSystemStatus(
        instance_id="different-instance-id", version="2.0.0"
    )
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_RECONFIGURE,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")
    expect(config_entry.data[CONF_API_TOKEN]).to_equal("test_api_token")
    expect(config_entry.data[CONF_URL]).to_equal("https://127.0.0.1:9000/")
    expect(len(setup_entry.mock_calls)).to_equal(0)


@test.cases(
    test.case("auth_error", exception=PortainerAuthenticationError, reason="invalid_auth"),
    test.case("connection_error", exception=PortainerConnectionError, reason="cannot_connect"),
    test.case("timeout_error", exception=PortainerTimeoutError, reason="timeout_connect"),
    test.case("other_exception", exception=Exception("Some other error"), reason="unknown"),
)
async def full_flow_reconfigure_exceptions(
    exception: Exception,
    reason: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_portainer_client),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the reconfigure flow with exceptions."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    client.portainer_system_status.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_RECONFIGURE,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": reason})

    client.portainer_system_status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_RECONFIGURE,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_API_TOKEN]).to_equal("new_api_key")
    expect(config_entry.data[CONF_URL]).to_equal("https://new_domain:9000/")
    expect(config_entry.data[CONF_VERIFY_SSL]).to_be(True)
    expect(len(setup_entry.mock_calls)).to_equal(1)
