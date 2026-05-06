"""Test the SystemNexa2 config flow."""

from ipaddress import ip_address
import socket
from unittest.mock import AsyncMock, MagicMock, patch

from sn2 import InformationData, InformationUpdate
from tryke import Depends, expect, fixture, test

from homeassistant.components.systemnexa2 import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_DEVICE_ID, CONF_HOST, CONF_MODEL, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    mock_config_entry,
    mock_patch_get_host,
    mock_setup_entry,
    mock_system_nexa_2_device,
    mock_zeroconf_discovery_info,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _device: MagicMock = Depends(mock_system_nexa_2_device),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Outdoor Smart Plug (WPO-01)")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "10.0.0.131",
            CONF_NAME: "Outdoor Smart Plug",
            CONF_DEVICE_ID: "aabbccddee02",
            CONF_MODEL: "WPO-01",
        }
    )
    expect(result["result"].unique_id).to_equal("aabbccddee02")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _device: MagicMock = Depends(mock_system_nexa_2_device),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if the device is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("cannot_connect", exception=TimeoutError, error_key="cannot_connect"),
    test.case("unknown", exception=RuntimeError, error_key="unknown"),
)
async def connection_error_and_recovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device: MagicMock = Depends(mock_system_nexa_2_device),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: type[Exception],
    error_key: str,
) -> None:
    """Test connection error handling and recovery."""
    device.return_value.get_info.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_key})

    inner = device.return_value
    inner.get_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Outdoor Smart Plug (WPO-01)")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def empty_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _device: MagicMock = Depends(mock_system_nexa_2_device),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test invalid hostname/IP address handling."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: ""}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_host"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def invalid_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _device: MagicMock = Depends(mock_system_nexa_2_device),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test invalid hostname/IP address handling."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.systemnexa2.config_flow.socket.gethostbyname",
        side_effect=socket.gaierror(-2, "Name or service not known"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "invalid-hostname.local"}
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_host"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def valid_hostname(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _device: MagicMock = Depends(mock_system_nexa_2_device),
    _patch_host: MagicMock = Depends(mock_patch_get_host),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test valid hostname handling."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "valid-hostname.local"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Outdoor Smart Plug (WPO-01)")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "valid-hostname.local",
            CONF_NAME: "Outdoor Smart Plug",
            CONF_DEVICE_ID: "aabbccddee02",
            CONF_MODEL: "WPO-01",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def unsupported_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device: MagicMock = Depends(mock_system_nexa_2_device),
) -> None:
    """Test unsupported device model handling."""
    device.is_device_supported.return_value = (False, "Err")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unsupported_model")
    expect(result["description_placeholders"]).to_equal(
        {
            "model": "WPO-01",
            "sw_version": "Test Model Version",
        }
    )


@test
async def zeroconf_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _device: MagicMock = Depends(mock_system_nexa_2_device),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    discovery_info: ZeroconfServiceInfo = Depends(mock_zeroconf_discovery_info),
) -> None:
    """Test zeroconf discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("systemnexa2_test (WPO-01)")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "10.0.0.131",
            CONF_NAME: "systemnexa2_test",
            CONF_DEVICE_ID: "aabbccddee02",
            CONF_MODEL: "WPO-01",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def zeroconf_discovery_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _device: MagicMock = Depends(mock_system_nexa_2_device),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    discovery_info: ZeroconfServiceInfo = Depends(mock_zeroconf_discovery_info),
) -> None:
    """Test we abort zeroconf discovery if the device is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def device_with_none_values(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device: MagicMock = Depends(mock_system_nexa_2_device),
) -> None:
    """Test device with None values in info is rejected."""
    inner = device.return_value
    inner.info_data = InformationData(
        name="Outdoor Smart Plug",
        model="WPO-01",
        unique_id=None,
        sw_version="Test Model Version",
        hw_version="Test HW Version",
        wifi_dbm=-50,
        wifi_ssid="Test WiFi SSID",
        dimmable=False,
    )
    inner.get_info.return_value = InformationUpdate(information=inner.info_data)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unsupported_model")


@test
async def zeroconf_discovery_none_values(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf discovery with None property values is rejected."""
    discovery_info = ZeroconfServiceInfo(
        ip_address=ip_address("10.0.0.131"),
        ip_addresses=[ip_address("10.0.0.131")],
        hostname="systemnexa2_test.local.",
        name="systemnexa2_test._systemnexa2._tcp.local.",
        port=80,
        type="_systemnexa2._tcp.local.",
        properties={
            "id": None,
            "model": "WPO-01",
            "version": "1.0.0",
        },
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unsupported_model")


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _device: MagicMock = Depends(mock_system_nexa_2_device),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguration flow."""
    config_entry.add_to_hass(hass)

    expect(config_entry.data[CONF_HOST] != "10.0.0.132").to_be(True)

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.132"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_HOST]).to_equal("10.0.0.132")
    expect(config_entry.data[CONF_DEVICE_ID]).to_equal("aabbccddee02")
    expect(config_entry.data[CONF_MODEL]).to_equal("WPO-01")
    expect(config_entry.data[CONF_NAME]).to_equal("Outdoor Smart Plug")


@test
async def reconfigure_flow_invalid_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguration flow with invalid host."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    with patch(
        "homeassistant.components.systemnexa2.config_flow.socket.gethostbyname",
        side_effect=socket.gaierror(-2, "Name or service not known"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "invalid_hostname"},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_host"})


@test
async def reconfigure_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    device: MagicMock = Depends(mock_system_nexa_2_device),
) -> None:
    """Test reconfiguration flow with connection error."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    device.initiate_device.side_effect = TimeoutError("Connection failed")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.132"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    device.initiate_device.side_effect = Exception("Unknown")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.132"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown"})


@test
async def reconfigure_flow_wrong_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    device: MagicMock = Depends(mock_system_nexa_2_device),
) -> None:
    """Test reconfiguration flow with different device."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    different_device_info = InformationData(
        name="Different Device",
        model="Test Model",
        unique_id="different_device_id",
        sw_version="Test Model Version",
        hw_version="Test HW Version",
        wifi_dbm=-50,
        wifi_ssid="Test WiFi SSID",
        dimmable=False,
    )
    device.return_value.get_info.return_value = InformationUpdate(
        information=different_device_info
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.132"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_device")
