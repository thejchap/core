"""Test the LibreHardwareMonitor config flow."""

from unittest.mock import AsyncMock

from librehardwaremonitor_api import (
    LibreHardwareMonitorConnectionError,
    LibreHardwareMonitorNoDevicesError,
    LibreHardwareMonitorUnauthorizedError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.libre_hardware_monitor.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    AUTH_INPUT,
    REAUTH_INPUT,
    VALID_CONFIG,
    VALID_CONFIG_WITH_AUTH,
    mock_auth_config_entry,
    mock_config_entry,
    mock_lhm_client,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_mn: None = Depends(mock_network)) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def create_entry_without_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_lhm_client: AsyncMock = Depends(mock_lhm_client),
) -> None:
    """Test that a complete config entry is created."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=VALID_CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_be(None)

    created_config_entry = result["result"]
    expect(created_config_entry.title).to_equal(
        f"GAMING-PC ({VALID_CONFIG[CONF_HOST]}:{VALID_CONFIG[CONF_PORT]})"
    )
    expect(created_config_entry.data).to_equal(VALID_CONFIG)

    expect(mock_setup_entry.call_count).to_equal(1)


@test
async def create_entry_with_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_lhm_client: AsyncMock = Depends(mock_lhm_client),
) -> None:
    """Test that a complete config entry is created with authentication credentials."""
    mock_lhm_client.get_data.side_effect = LibreHardwareMonitorUnauthorizedError()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=VALID_CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_lhm_client.get_data.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=AUTH_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_be(None)

    created_config_entry = result["result"]
    expect(created_config_entry.data).to_equal(VALID_CONFIG_WITH_AUTH)

    expect(mock_setup_entry.call_count).to_equal(1)


@test.cases(
    test.case("cannot_connect", LibreHardwareMonitorConnectionError, "cannot_connect"),
    test.case("no_devices", LibreHardwareMonitorNoDevicesError, "no_devices"),
)
async def errors_and_flow_recovery(
    side_effect: type[Exception],
    error_text: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_lhm_client: AsyncMock = Depends(mock_lhm_client),
) -> None:
    """Test that errors are shown as expected."""
    mock_lhm_client.get_data.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=VALID_CONFIG
    )

    expect(result["errors"]).to_equal({"base": error_text})
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    mock_lhm_client.get_data.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=VALID_CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(mock_setup_entry.call_count).to_equal(1)


@test
async def lhm_server_already_exists_without_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we only allow a single entry per server."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=VALID_CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(mock_setup_entry.call_count).to_equal(0)


@test
async def lhm_server_already_exists_with_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_auth_config_entry: MockConfigEntry = Depends(mock_auth_config_entry),
) -> None:
    """Test auth has no influence on single entry per server."""
    mock_auth_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=VALID_CONFIG
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(mock_setup_entry.call_count).to_equal(0)


@test
async def reauth_no_previous_credentials(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_lhm_client: AsyncMock = Depends(mock_lhm_client),
) -> None:
    """Test reauth flow when web server did not require auth before."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        REAUTH_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data).to_equal({**VALID_CONFIG, **REAUTH_INPUT})
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def reauth_with_previous_credentials(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_auth_config_entry: MockConfigEntry = Depends(mock_auth_config_entry),
    _mock_lhm_client: AsyncMock = Depends(mock_lhm_client),
) -> None:
    """Test reauth flow when web server credentials changed."""
    mock_auth_config_entry.add_to_hass(hass)

    result = await mock_auth_config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        REAUTH_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_auth_config_entry.data).to_equal({**VALID_CONFIG, **REAUTH_INPUT})
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case("cannot_connect", LibreHardwareMonitorConnectionError, "cannot_connect"),
    test.case("invalid_auth", LibreHardwareMonitorUnauthorizedError, "invalid_auth"),
    test.case("no_devices", LibreHardwareMonitorNoDevicesError, "no_devices"),
)
async def reauth_errors(
    side_effect: type[Exception],
    error_text: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_lhm_client: AsyncMock = Depends(mock_lhm_client),
) -> None:
    """Test reauth flow errors."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_lhm_client.get_data.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        REAUTH_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_text})

    mock_lhm_client.get_data.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        REAUTH_INPUT,
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data).to_equal({**VALID_CONFIG, **REAUTH_INPUT})
    expect(len(hass.config_entries.async_entries())).to_equal(1)
