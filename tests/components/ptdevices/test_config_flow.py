"""Test the PTDevices config flow."""

from unittest.mock import AsyncMock

from aioptdevices import PTDevicesRequestError, PTDevicesUnauthorizedError
from aioptdevices.interface import PTDevicesResponse
from tryke import Depends, expect, fixture, test

from homeassistant.components.ptdevices.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_ptdevices_config_entry,
    mock_ptdevices_interface,
    mock_ptdevices_level,
    mock_ptdevices_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_ptdevices_setup_entry),
    _iface: AsyncMock = Depends(mock_ptdevices_interface),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def flow_success(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    mock_ptdevices_iface: AsyncMock = Depends(mock_ptdevices_interface),
) -> None:
    """Test a successful creation of config entries via user configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_TOKEN: "test-api-token"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("User Name")
    expect(result["result"].unique_id).to_equal("1234")
    expect(result["data"]).to_equal(
        {
            CONF_API_TOKEN: "test-api-token",
        }
    )

    expect(len(mock_ptdevices_iface.mock_calls)).to_equal(1)


@test
async def flow_duplicate_device(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    config_entry: MockConfigEntry = Depends(mock_ptdevices_config_entry),
) -> None:
    """Test a duplicate config flow."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_TOKEN: "test-api-token"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "unauthorized",
        exception=PTDevicesUnauthorizedError,
        error="invalid_access_token",
    ),
    test.case(
        "request_error",
        exception=PTDevicesRequestError,
        error="cannot_connect",
    ),
    test.case(
        "unknown",
        exception=Exception,
        error="unknown",
    ),
)
async def flow_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    mock_ptdevices_iface: AsyncMock = Depends(mock_ptdevices_interface),
    *,
    exception: type[Exception],
    error: str,
) -> None:
    """Test flow errors."""
    mock_ptdevices_iface.get_data.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_TOKEN: "test-api-token"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_ptdevices_iface.get_data.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_TOKEN: "test-api-token"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def flow_no_devices(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    mock_ptdevices_iface: AsyncMock = Depends(mock_ptdevices_interface),
    level: PTDevicesResponse = Depends(mock_ptdevices_level),
) -> None:
    """Test A flow with no devices in the account."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    # No devices
    mock_ptdevices_iface.get_data.return_value = PTDevicesResponse(
        code=200,
        body={},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_TOKEN: "test-api-token"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "no_devices_found"})

    # Reset the mock to the default return value
    mock_ptdevices_iface.get_data.return_value = level

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_TOKEN: "test-api-token"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
