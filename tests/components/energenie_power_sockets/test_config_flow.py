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

from ._fixtures import (
    demo_config_data,
    mock_get_device,
    mock_search_for_devices,
    valid_config_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_data: dict = Depends(demo_config_data),
    _get_device: MagicMock = Depends(mock_get_device),
    _search: MagicMock = Depends(mock_search_for_devices),
) -> None:
    """Test configuration flow initialized by the user."""
    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result1["type"]).to_be(FlowResultType.FORM)
    expect(not result1["errors"]).to_be(True)

    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"], user_input=config_data
    )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_flow_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(valid_config_entry),
    _get_device: MagicMock = Depends(mock_get_device),
    _search: MagicMock = Depends(mock_search_for_devices),
) -> None:
    """Test the flow when device has been already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_DEVICE_API_ID: config_entry.data[CONF_DEVICE_API_ID]},
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_flow_no_new_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(valid_config_entry),
    _get_device: MagicMock = Depends(mock_get_device),
    _search: MagicMock = Depends(mock_search_for_devices),
) -> None:
    """Test the flow when the found device has been already included."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=None,
    )

    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_device")


@test
async def user_flow_no_device_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_data: dict = Depends(demo_config_data),
    _get_device: MagicMock = Depends(mock_get_device),
    search: MagicMock = Depends(mock_search_for_devices),
) -> None:
    """Test configuration flow when no device is found."""
    search.return_value = []

    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result1["type"]).to_be(FlowResultType.ABORT)
    expect(result1["reason"]).to_equal("no_device")


@test
async def user_flow_device_not_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_data: dict = Depends(demo_config_data),
    get_device: MagicMock = Depends(mock_get_device),
    _search: MagicMock = Depends(mock_search_for_devices),
) -> None:
    """Test configuration flow when the given device_id does not match any found devices."""
    get_device.return_value = None

    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result1["type"]).to_be(FlowResultType.FORM)
    expect(not result1["errors"]).to_be(True)

    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"], user_input=config_data
    )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("device_not_found")


@test
async def user_flow_no_usb_access(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    get_device: MagicMock = Depends(mock_get_device),
    search: MagicMock = Depends(mock_search_for_devices),
) -> None:
    """Test configuration flow when USB devices can't be accessed."""
    get_device.return_value = None
    search.side_effect = UsbError

    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result1["type"]).to_be(FlowResultType.ABORT)
    expect(result1["reason"]).to_equal("usb_error")
