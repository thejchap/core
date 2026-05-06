"""Tests for the Homevolt config flow."""

from ipaddress import IPv4Address
from unittest.mock import AsyncMock, MagicMock

from homevolt import HomevoltAuthenticationError, HomevoltConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.homevolt.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    mock_config_entry,
    mock_homevolt_client,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DISCOVERY_INFO = ZeroconfServiceInfo(
    ip_address=IPv4Address("192.168.1.123"),
    ip_addresses=[IPv4Address("192.168.1.123")],
    port=80,
    hostname="homevolt.local.",
    type="_http._tcp.local.",
    name="homevolt._http._tcp.local.",
    properties={},
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: MagicMock = Depends(mock_homevolt_client),
) -> None:
    """Test a complete successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    user_input = {CONF_HOST: "192.168.1.100"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Homevolt")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.100", CONF_PASSWORD: None})
    expect(result["result"].unique_id).to_equal("40580137858664")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def flow_auth_error_then_password_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: MagicMock = Depends(mock_homevolt_client),
) -> None:
    """Test flow when authentication is required."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    user_input = {CONF_HOST: "192.168.1.100"}

    client.update_info.side_effect = HomevoltAuthenticationError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("credentials")
    expect(result["errors"]).to_equal({})

    client.update_info.side_effect = None

    password_input = {CONF_PASSWORD: "test-password"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], password_input
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Homevolt")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.100",
            CONF_PASSWORD: "test-password",
        }
    )
    expect(result["result"].unique_id).to_equal("40580137858664")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "connection", exception=HomevoltConnectionError, expected_error="cannot_connect"
    ),
    test.case("unknown", exception=Exception, expected_error="unknown"),
)
async def step_user_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: MagicMock = Depends(mock_homevolt_client),
    *,
    exception: type[Exception],
    expected_error: str,
) -> None:
    """Test error cases for the user step with recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    user_input = {CONF_HOST: "192.168.1.100"}

    client.update_info.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": expected_error})

    client.update_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Homevolt")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.100", CONF_PASSWORD: None})
    expect(result["result"].unique_id).to_equal("40580137858664")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: MagicMock = Depends(mock_homevolt_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that a duplicate device_id aborts the flow."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    user_input = {CONF_HOST: "192.168.1.200"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def credentials_step_invalid_password(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: MagicMock = Depends(mock_homevolt_client),
) -> None:
    """Test invalid password in credentials step shows error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    user_input = {CONF_HOST: "192.168.1.100"}

    client.update_info.side_effect = HomevoltAuthenticationError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("credentials")

    password_input = {CONF_PASSWORD: "wrong-password"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], password_input
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("credentials")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    client.update_info.side_effect = None

    password_input = {CONF_PASSWORD: "correct-password"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], password_input
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Homevolt")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.100",
            CONF_PASSWORD: "correct-password",
        }
    )
    expect(result["result"].unique_id).to_equal("40580137858664")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def reauth_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: MagicMock = Depends(mock_homevolt_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test successful reauthentication flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["description_placeholders"]).to_equal(
        {
            "host": "127.0.0.1",
            "name": "Homevolt",
        }
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new-password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.unique_id).to_equal("40580137858664")
    expect(config_entry.data).to_equal(
        {
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "new-password",
        }
    )


@test.cases(
    test.case(
        "auth", exception=HomevoltAuthenticationError, expected_error="invalid_auth"
    ),
    test.case(
        "connection", exception=HomevoltConnectionError, expected_error="cannot_connect"
    ),
    test.case("unknown", exception=Exception, expected_error="unknown"),
)
async def reauth_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: MagicMock = Depends(mock_homevolt_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: type[Exception],
    expected_error: str,
) -> None:
    """Test reauthentication flow with errors and recovery."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    client.update_info.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "wrong-password"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": expected_error})

    client.update_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "correct-password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data).to_equal(
        {
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "correct-password",
        }
    )


@test
async def zeroconf_confirm_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: MagicMock = Depends(mock_homevolt_client),
) -> None:
    """Test zeroconf flow shows confirm step before creating entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["description_placeholders"]).to_equal({"host": "192.168.1.123"})

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Homevolt")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.123", CONF_PASSWORD: None})
    expect(result["result"].unique_id).to_equal("40580137858664")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def zeroconf_duplicate_aborts(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: MagicMock = Depends(mock_homevolt_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test zeroconf flow aborts when unique id is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.123")


@test
async def zeroconf_confirm_with_password_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: MagicMock = Depends(mock_homevolt_client),
) -> None:
    """Test zeroconf confirm collects password and creates entry when auth is required."""
    client.update_info.side_effect = HomevoltAuthenticationError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["description_placeholders"]).to_equal({"host": "192.168.1.123"})

    client.update_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "test-password"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Homevolt")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.123",
            CONF_PASSWORD: "test-password",
        }
    )
    expect(result["result"].unique_id).to_equal("40580137858664")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def zeroconf_confirm_with_password_invalid_then_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: MagicMock = Depends(mock_homevolt_client),
) -> None:
    """Test zeroconf confirm shows error on invalid password, then succeeds."""
    client.update_info.side_effect = HomevoltAuthenticationError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "wrong-password"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    client.update_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "correct-password"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Homevolt")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.123",
            CONF_PASSWORD: "correct-password",
        }
    )
    expect(result["result"].unique_id).to_equal("40580137858664")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "connection_error",
        exception=HomevoltConnectionError,
        expected_reason="cannot_connect",
    ),
    test.case(
        "unknown_error",
        exception=Exception("Unexpected error"),
        expected_reason="unknown",
    ),
)
async def zeroconf_error_aborts(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: MagicMock = Depends(mock_homevolt_client),
    *,
    exception: object,
    expected_reason: str,
) -> None:
    """Test zeroconf flow aborts on error during discovery."""
    client.update_info.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(expected_reason)
