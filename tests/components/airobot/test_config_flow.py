"""Test the Airobot config flow."""

from unittest.mock import AsyncMock

from pyairobotrest.exceptions import (
    AirobotAuthError,
    AirobotConnectionError,
    AirobotError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.airobot.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import mock_airobot_client, mock_config_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_USER_INPUT = {
    CONF_HOST: "192.168.1.100",
    CONF_USERNAME: "T01A1B2C3",
    CONF_PASSWORD: "test-password",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(mock_airobot_client),
) -> None:
    """Test user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Test Thermostat")
    expect(result["data"]).to_equal(TEST_USER_INPUT)
    expect(result["result"].unique_id).to_equal("T01A1B2C3")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "auth", exception=AirobotAuthError("Authentication failed"), error_base="invalid_auth"
    ),
    test.case(
        "connection",
        exception=AirobotConnectionError("Connection failed"),
        error_base="cannot_connect",
    ),
    test.case(
        "generic", exception=AirobotError("Generic error"), error_base="cannot_connect"
    ),
    test.case(
        "unknown", exception=Exception("Unexpected error"), error_base="unknown"
    ),
)
async def form_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_airobot_client),
    *,
    exception: Exception,
    error_base: str,
) -> None:
    """Test we handle various errors in user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    client.get_settings.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_base})

    client.get_settings.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Test Thermostat")
    expect(result["data"]).to_equal(TEST_USER_INPUT)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(mock_airobot_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate detection."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def dhcp_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(mock_airobot_client),
) -> None:
    """Test DHCP discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.100",
            macaddress="b8d61aabcdef",
            hostname="airobot-thermostat-t01a1b2c3",
        ),
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("dhcp_confirm")
    expect(result["description_placeholders"]).to_equal(
        {
            "host": "192.168.1.100",
            "device_id": "T01A1B2C3",
        }
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "test-password"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Test Thermostat")
    expect(result["data"][CONF_HOST]).to_equal("192.168.1.100")
    expect(result["data"][CONF_USERNAME]).to_equal("T01A1B2C3")
    expect(result["data"][CONF_PASSWORD]).to_equal("test-password")
    expect(result["data"][CONF_MAC]).to_equal("b8d61aabcdef")


@test.cases(
    test.case(
        "auth",
        exception=AirobotAuthError("Invalid credentials"),
        error_base="invalid_auth",
    ),
    test.case(
        "connection",
        exception=AirobotConnectionError("Connection failed"),
        error_base="cannot_connect",
    ),
    test.case(
        "unknown", exception=Exception("Unknown error"), error_base="unknown"
    ),
)
async def dhcp_discovery_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_airobot_client),
    *,
    exception: Exception,
    error_base: str,
) -> None:
    """Test DHCP discovery with error handling."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.100",
            macaddress="aabbccddeeff",
            hostname="airobot-thermostat-t01d4e5f6",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("dhcp_confirm")

    client.get_statuses.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "wrong"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_base})

    client.get_statuses.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "test-password"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Test Thermostat")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def dhcp_discovery_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(mock_airobot_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test DHCP discovery with duplicate device."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.101",
            macaddress="b8d61aabcdef",
            hostname="airobot-thermostat-t01a1b2c3",
        ),
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.101")


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(mock_airobot_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauthentication flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["description_placeholders"]["username"]).to_equal("T01A1B2C3")
    expect(result["description_placeholders"]["host"]).to_equal("192.168.1.100")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new-password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new-password")


@test.cases(
    test.case(
        "auth",
        exception=AirobotAuthError("Invalid credentials"),
        error_base="invalid_auth",
    ),
    test.case(
        "connection",
        exception=AirobotConnectionError("Connection failed"),
        error_base="cannot_connect",
    ),
    test.case(
        "unknown", exception=Exception("Unknown error"), error_base="unknown"
    ),
)
async def reauth_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_airobot_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: Exception,
    error_base: str,
) -> None:
    """Test reauthentication flow with errors."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    client.get_statuses.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "wrong-password"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_base})

    client.get_statuses.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new-password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new-password")


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: AsyncMock = Depends(mock_airobot_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguration flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.200",
            CONF_USERNAME: "T01A1B2C3",
            CONF_PASSWORD: "new-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.200")
    expect(config_entry.data[CONF_USERNAME]).to_equal("T01A1B2C3")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new-password")


@test
async def reconfigure_flow_wrong_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_airobot_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguration flow with wrong device."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    client.get_settings.return_value.device_name = "Different Device"
    client.get_statuses.return_value.device_id = "T01DIFFERENT"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.200",
            CONF_USERNAME: "T01DIFFERENT",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_device")


@test.cases(
    test.case(
        "auth",
        exception=AirobotAuthError("Invalid credentials"),
        error_base="invalid_auth",
    ),
    test.case(
        "connection",
        exception=AirobotConnectionError("Connection failed"),
        error_base="cannot_connect",
    ),
    test.case(
        "unknown", exception=Exception("Unknown error"), error_base="unknown"
    ),
)
async def reconfigure_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_airobot_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: Exception,
    error_base: str,
) -> None:
    """Test reconfiguration flow with errors."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    client.get_statuses.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.200",
            CONF_USERNAME: "T01A1B2C3",
            CONF_PASSWORD: "wrong-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_base})

    client.get_statuses.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.200",
            CONF_USERNAME: "T01A1B2C3",
            CONF_PASSWORD: "new-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.200")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new-password")
