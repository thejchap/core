"""Test the config flow for Proxmox VE."""

from typing import Any
from unittest.mock import MagicMock

from proxmoxer import AuthenticationError
from proxmoxer.core import ResourceException
import requests
from requests.exceptions import ConnectTimeout, SSLError
from tryke import Depends, expect, fixture, test

from homeassistant.components.proxmoxve import CONF_AUTH_METHOD, CONF_HOST, CONF_REALM
from homeassistant.components.proxmoxve.const import (
    CONF_NODE,
    CONF_NODES,
    CONF_TOKEN,
    CONF_TOKEN_ID,
    CONF_TOKEN_SECRET,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_PORT, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    MOCK_TEST_CONFIG,
    MOCK_TEST_OTHER_CONFIG,
    MOCK_TEST_TOKEN_CONFIG,
    MOCK_TEST_TOKEN_OTHER_CONFIG,
    mock_config_entry,
    mock_proxmox_client,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_USER_STEP = {
    CONF_AUTH_METHOD: "pam",
    CONF_HOST: "127.0.0.1",
    CONF_USERNAME: "test_user",
    CONF_VERIFY_SSL: True,
    CONF_PORT: 8006,
    CONF_TOKEN: False,
}

MOCK_USER_AUTH_STEP_PASSWORD = {
    CONF_PASSWORD: "test_password",
}

MOCK_USER_STEP_TOKEN = {
    **MOCK_USER_STEP,
    CONF_TOKEN: True,
}

MOCK_USER_AUTH_STEP_TOKEN = {
    CONF_TOKEN_ID: "test_token_id",
    CONF_TOKEN_SECRET: "test_token_secret",
}

MOCK_USER_STEP_OTHER = {
    **MOCK_USER_STEP,
    CONF_AUTH_METHOD: "other",
}

MOCK_USER_AUTH_STEP_OTHER = {
    **MOCK_USER_AUTH_STEP_PASSWORD,
    CONF_REALM: "test_realm",
}

MOCK_USER_STEP_OTHER_TOKEN = {
    **MOCK_USER_STEP_TOKEN,
    CONF_AUTH_METHOD: "other",
}

MOCK_USER_AUTH_STEP_OTHER_TOKEN = {
    **MOCK_USER_AUTH_STEP_TOKEN,
    CONF_REALM: "test_realm",
}

MOCK_USER_SETUP = {CONF_NODES: ["pve1"]}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local fixture executor anchor."""


@test.cases(
    test.case("pam_password", mock_user_step=MOCK_USER_STEP, mock_user_auth_step=MOCK_USER_AUTH_STEP_PASSWORD, mock_test_config=MOCK_TEST_CONFIG),
    test.case("pam_token", mock_user_step=MOCK_USER_STEP_TOKEN, mock_user_auth_step=MOCK_USER_AUTH_STEP_TOKEN, mock_test_config=MOCK_TEST_TOKEN_CONFIG),
    test.case("other_password", mock_user_step=MOCK_USER_STEP_OTHER, mock_user_auth_step=MOCK_USER_AUTH_STEP_OTHER, mock_test_config=MOCK_TEST_OTHER_CONFIG),
    test.case("other_token", mock_user_step=MOCK_USER_STEP_OTHER_TOKEN, mock_user_auth_step=MOCK_USER_AUTH_STEP_OTHER_TOKEN, mock_test_config=MOCK_TEST_TOKEN_OTHER_CONFIG),
)
async def form(
    *,
    mock_user_step: dict[str, Any],
    mock_user_auth_step: dict[str, Any],
    mock_test_config: dict[str, Any],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(mock_proxmox_client),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=mock_user_step
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user_auth")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=mock_user_auth_step
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("127.0.0.1")
    expect(result["data"]).to_equal(mock_test_config)


@test.cases(
    test.case("auth_error", exception=AuthenticationError("Invalid credentials"), reason="invalid_auth"),
    test.case("ssl_error", exception=SSLError("SSL handshake failed"), reason="ssl_error"),
    test.case("connect_timeout", exception=ConnectTimeout("Connection timed out"), reason="connect_timeout"),
    test.case("api_error", exception=ResourceException("500", "status_message", "content"), reason="api_error_no_details"),
    test.case("connection_error", exception=requests.exceptions.ConnectionError("Connection error"), reason="cannot_connect"),
)
async def form_exceptions(
    *,
    exception: Exception,
    reason: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_proxmox_client),
) -> None:
    """Test we handle all exceptions."""
    client._mock_api_cf.side_effect = exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_STEP,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user_auth")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_USER_AUTH_STEP_PASSWORD,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": reason})

    client._mock_api_cf.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_AUTH_STEP_PASSWORD
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(mock_proxmox_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort on duplicate entry."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_STEP
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user_auth")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_AUTH_STEP_PASSWORD
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.skip("test_form_node_exceptions: not yet ported (mock injection on nodes.get)")
async def form_node_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub."""


@test.skip("test_form_exceptions_qemu: not yet ported (qemu mock injection)")
async def form_exceptions_qemu(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub."""


@test.skip("test_form_no_nodes_exception: not yet ported")
async def form_no_nodes_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub."""


@test.skip("test_import_flow: not yet ported")
async def import_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub."""


@test.skip("test_import_flow_exceptions: not yet ported")
async def import_flow_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub."""


@test.skip("test_full_flow_reconfigure: not yet ported")
async def full_flow_reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub."""


@test.skip("test_full_flow_reconfigure_match_entries: not yet ported")
async def full_flow_reconfigure_match_entries(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub."""


@test.skip("test_full_flow_reconfigure_exceptions: not yet ported")
async def full_flow_reconfigure_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub."""


@test.skip("test_full_flow_reauth: not yet ported")
async def full_flow_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub."""


@test.skip("test_full_flow_reauth_token_other: not yet ported")
async def full_flow_reauth_token_other(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub."""


@test.skip("test_full_flow_reauth_exceptions: not yet ported")
async def full_flow_reauth_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub."""


@test.skip("test_form_offline_node_skipped: not yet ported")
async def form_offline_node_skipped(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub."""
