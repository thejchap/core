"""Test the Motionblinds Bluetooth config flow."""

from unittest.mock import AsyncMock, Mock, patch

from motionblindsble.const import MotionBlindType
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.bluetooth.models import BluetoothServiceInfoBleak
from homeassistant.components.motionblinds_ble import const
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    address,
    blind_type,
    display_name,
    local_name,
    mac_code,
    mock_config_entry,
    mock_setup_entry,
    motionblinds_ble_connect,
    service_info,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    enable_bluetooth,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def config_flow_manual_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _connect: tuple[AsyncMock, Mock] = Depends(motionblinds_ble_connect),
    _setup: AsyncMock = Depends(mock_setup_entry),
    blind_type: MotionBlindType = Depends(blind_type),
    mac_code: str = Depends(mac_code),
    address: str = Depends(address),
    local_name: str = Depends(local_name),
    display_name: str = Depends(display_name),
) -> None:
    """Successful flow manually initialized by the user."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_MAC_CODE: mac_code},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_BLIND_TYPE: blind_type.name.lower()},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(display_name)
    expect(result["data"]).to_equal(
        {
            CONF_ADDRESS: address,
            const.CONF_LOCAL_NAME: local_name,
            const.CONF_MAC_CODE: mac_code,
            const.CONF_BLIND_TYPE: blind_type.name.lower(),
        }
    )
    expect(result["options"]).to_equal({})


@test
async def config_flow_manual_error_invalid_mac(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _connect: tuple[AsyncMock, Mock] = Depends(motionblinds_ble_connect),
    _setup: AsyncMock = Depends(mock_setup_entry),
    mac_code: str = Depends(mac_code),
    address: str = Depends(address),
    local_name: str = Depends(local_name),
    display_name: str = Depends(display_name),
    blind_type: MotionBlindType = Depends(blind_type),
) -> None:
    """Invalid MAC code error flow manually initialized by the user."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_MAC_CODE: "AABBCC"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": const.ERROR_INVALID_MAC_CODE})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_MAC_CODE: mac_code},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_BLIND_TYPE: blind_type.name.lower()},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(display_name)
    expect(result["data"]).to_equal(
        {
            CONF_ADDRESS: address,
            const.CONF_LOCAL_NAME: local_name,
            const.CONF_MAC_CODE: mac_code,
            const.CONF_BLIND_TYPE: blind_type.name.lower(),
        }
    )
    expect(result["options"]).to_equal({})


@test
async def config_flow_manual_error_no_bluetooth_adapter(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _connect: tuple[AsyncMock, Mock] = Depends(motionblinds_ble_connect),
    mac_code: str = Depends(mac_code),
) -> None:
    """No Bluetooth adapter error flow manually initialized by the user."""
    with patch(
        "homeassistant.components.motionblinds_ble.config_flow.bluetooth.async_scanner_count",
        return_value=0,
    ):
        result = await hass.config_entries.flow.async_init(
            const.DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(const.ERROR_NO_BLUETOOTH_ADAPTER)

    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.motionblinds_ble.config_flow.bluetooth.async_scanner_count",
        return_value=0,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {const.CONF_MAC_CODE: mac_code},
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(const.ERROR_NO_BLUETOOTH_ADAPTER)


@test
async def config_flow_manual_error_could_not_find_motor(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    connect: tuple[AsyncMock, Mock] = Depends(motionblinds_ble_connect),
    mac_code: str = Depends(mac_code),
    local_name: str = Depends(local_name),
    display_name: str = Depends(display_name),
    address: str = Depends(address),
    blind_type: MotionBlindType = Depends(blind_type),
) -> None:
    """Could not find motor error flow manually initialized by the user."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    connect[1].name = "WRONG_NAME"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_MAC_CODE: mac_code},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": const.ERROR_COULD_NOT_FIND_MOTOR})

    connect[1].name = local_name
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_MAC_CODE: mac_code},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_BLIND_TYPE: blind_type.name.lower()},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(display_name)
    expect(result["data"]).to_equal(
        {
            CONF_ADDRESS: address,
            const.CONF_LOCAL_NAME: local_name,
            const.CONF_MAC_CODE: mac_code,
            const.CONF_BLIND_TYPE: blind_type.name.lower(),
        }
    )
    expect(result["options"]).to_equal({})


@test
async def config_flow_manual_error_no_devices_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    connect: tuple[AsyncMock, Mock] = Depends(motionblinds_ble_connect),
    mac_code: str = Depends(mac_code),
) -> None:
    """No devices found error flow manually initialized by the user."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    connect[0].discover.return_value = []
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_MAC_CODE: mac_code},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(const.ERROR_NO_DEVICES_FOUND)


@test
async def config_flow_bluetooth_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _connect: tuple[AsyncMock, Mock] = Depends(motionblinds_ble_connect),
    mac_code: str = Depends(mac_code),
    service_info: BluetoothServiceInfoBleak = Depends(service_info),
    address: str = Depends(address),
    local_name: str = Depends(local_name),
    display_name: str = Depends(display_name),
    blind_type: MotionBlindType = Depends(blind_type),
) -> None:
    """Successful bluetooth discovery flow."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=service_info,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {const.CONF_BLIND_TYPE: blind_type.name.lower()},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(display_name)
    expect(result["data"]).to_equal(
        {
            CONF_ADDRESS: address,
            const.CONF_LOCAL_NAME: local_name,
            const.CONF_MAC_CODE: mac_code,
            const.CONF_BLIND_TYPE: blind_type.name.lower(),
        }
    )
    expect(result["options"]).to_equal({})


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the options flow."""
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            const.OPTION_PERMANENT_CONNECTION: True,
            const.OPTION_DISCONNECT_TIME: 10,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
