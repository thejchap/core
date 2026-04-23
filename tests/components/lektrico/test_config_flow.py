"""Tests for the Lektrico Charging Station config flow."""

import dataclasses
from ipaddress import ip_address
from unittest.mock import AsyncMock

from lektricowifi import DeviceConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.lektrico.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import (
    ATTR_HW_VERSION,
    ATTR_SERIAL_NUMBER,
    CONF_HOST,
    CONF_TYPE,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    MOCKED_DEVICE_BOARD_REV,
    MOCKED_DEVICE_IP_ADDRESS,
    MOCKED_DEVICE_SERIAL_NUMBER,
    MOCKED_DEVICE_TYPE,
    MOCKED_DEVICE_ZEROCONF_DATA,
    mock_config_entry,
    mock_device,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_mn: None = Depends(mock_network)) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def user_setup(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_device: AsyncMock = Depends(mock_device),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test manually setting up."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(SOURCE_USER)
    expect("flow_id" in result).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCKED_DEVICE_IP_ADDRESS},
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal(
        f"{MOCKED_DEVICE_TYPE}_{MOCKED_DEVICE_SERIAL_NUMBER}"
    )
    expect(result.get("data")).to_equal(
        {
            CONF_HOST: MOCKED_DEVICE_IP_ADDRESS,
            ATTR_SERIAL_NUMBER: MOCKED_DEVICE_SERIAL_NUMBER,
            CONF_TYPE: MOCKED_DEVICE_TYPE,
            ATTR_HW_VERSION: MOCKED_DEVICE_BOARD_REV,
        }
    )
    expect("result" in result).to_be(True)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(result.get("result").unique_id).to_equal(MOCKED_DEVICE_SERIAL_NUMBER)


@test
async def user_setup_already_exists(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_device: AsyncMock = Depends(mock_device),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test manually setting up when the device already exists."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCKED_DEVICE_IP_ADDRESS},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_setup_device_offline(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: AsyncMock = Depends(mock_device),
) -> None:
    """Test manually setting up when device is offline."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    mock_device.device_config.side_effect = DeviceConnectionError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCKED_DEVICE_IP_ADDRESS},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_HOST: "cannot_connect"})
    expect(result["step_id"]).to_equal("user")

    mock_device.device_config.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCKED_DEVICE_IP_ADDRESS},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def discovered_zeroconf(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_device: AsyncMock = Depends(mock_device),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we can setup when discovered from zeroconf."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=MOCKED_DEVICE_ZEROCONF_DATA,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)
    expect(result.get("step_id")).to_equal("confirm")

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: MOCKED_DEVICE_IP_ADDRESS,
            ATTR_SERIAL_NUMBER: MOCKED_DEVICE_SERIAL_NUMBER,
            CONF_TYPE: MOCKED_DEVICE_TYPE,
            ATTR_HW_VERSION: MOCKED_DEVICE_BOARD_REV,
        }
    )
    expect(result2["title"]).to_equal(
        f"{MOCKED_DEVICE_TYPE}_{MOCKED_DEVICE_SERIAL_NUMBER}"
    )


@test
async def zeroconf_setup_already_exists(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_device: AsyncMock = Depends(mock_device),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort zeroconf flow if device already configured."""
    mock_config_entry.add_to_hass(hass)
    zc_data_new_ip = dataclasses.replace(MOCKED_DEVICE_ZEROCONF_DATA)
    zc_data_new_ip.ip_address = ip_address(MOCKED_DEVICE_IP_ADDRESS)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=zc_data_new_ip,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def discovered_zeroconf_device_connection_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: AsyncMock = Depends(mock_device),
) -> None:
    """Test we can setup when discovered from zeroconf but device went offline."""
    mock_device.device_config.side_effect = DeviceConnectionError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=MOCKED_DEVICE_ZEROCONF_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")
