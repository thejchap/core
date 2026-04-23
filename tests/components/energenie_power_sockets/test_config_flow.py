"""Tests for Energenie-Power-Sockets config flow."""

from unittest.mock import MagicMock

from pyegps.exceptions import UsbError
from tryke import Depends, expect, fixture, test

from homeassistant.components.energenie_power_sockets.const import (
    CONF_DEVICE_API_ID,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.energenie_power_sockets._fixtures import (
    demo_config_data,
    mock_get_device,
    mock_search_for_devices,
    mock_zeroconf,
    pyegps_device_mock,
    valid_config_entry,
)
from tests.hass_fixtures import hass, mock_network

pyegps_device_mock = pyegps_device_mock  # noqa: F811


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def user_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    demo_config_data: dict = Depends(demo_config_data),
    _mock_get_device: MagicMock = Depends(mock_get_device),
    _mock_search_for_devices: MagicMock = Depends(mock_search_for_devices),
) -> None:
    """Test configuration flow initialized by the user."""
    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result1["type"] is FlowResultType.FORM).to_be(True)
    expect(bool(result1["errors"])).to_be(False)

    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"], user_input=demo_config_data
    )
    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)


@test
async def user_flow_already_exists(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    valid_config_entry: MockConfigEntry = Depends(valid_config_entry),
    _mock_get_device: MagicMock = Depends(mock_get_device),
    _mock_search_for_devices: MagicMock = Depends(mock_search_for_devices),
) -> None:
    """Test the flow when device has been already configured."""
    valid_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_DEVICE_API_ID: valid_config_entry.data[CONF_DEVICE_API_ID]},
    )

    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_flow_no_new_device(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    valid_config_entry: MockConfigEntry = Depends(valid_config_entry),
    _mock_get_device: MagicMock = Depends(mock_get_device),
    _mock_search_for_devices: MagicMock = Depends(mock_search_for_devices),
) -> None:
    """Test the flow when the found device has been already included."""
    valid_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=None,
    )

    await hass.async_block_till_done()

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("no_device")


@test
async def user_flow_no_device_found(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _demo_config_data: dict = Depends(demo_config_data),
    _mock_get_device: MagicMock = Depends(mock_get_device),
    mock_search_for_devices: MagicMock = Depends(mock_search_for_devices),
) -> None:
    """Test configuration flow when no device is found."""
    mock_search_for_devices.return_value = []

    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result1["type"] is FlowResultType.ABORT).to_be(True)
    expect(result1["reason"]).to_equal("no_device")


@test
async def user_flow_device_not_found(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    demo_config_data: dict = Depends(demo_config_data),
    mock_get_device: MagicMock = Depends(mock_get_device),
    _mock_search_for_devices: MagicMock = Depends(mock_search_for_devices),
) -> None:
    """Test configuration flow when the given device_id does not match any found devices."""
    mock_get_device.return_value = None

    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result1["type"] is FlowResultType.FORM).to_be(True)
    expect(bool(result1["errors"])).to_be(False)

    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"], user_input=demo_config_data
    )
    expect(result2["type"] is FlowResultType.ABORT).to_be(True)
    expect(result2["reason"]).to_equal("device_not_found")


@test
async def user_flow_no_usb_access(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_get_device: MagicMock = Depends(mock_get_device),
    mock_search_for_devices: MagicMock = Depends(mock_search_for_devices),
) -> None:
    """Test configuration flow when USB devices can't be accessed."""
    mock_get_device.return_value = None
    mock_search_for_devices.side_effect = UsbError

    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result1["type"] is FlowResultType.ABORT).to_be(True)
    expect(result1["reason"]).to_equal("usb_error")
