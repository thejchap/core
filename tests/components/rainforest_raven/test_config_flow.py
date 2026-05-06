"""Test Rainforest RAVEn config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.rainforest_raven.const import DOMAIN
from homeassistant.config_entries import SOURCE_USB, SOURCE_USER
from homeassistant.const import CONF_DEVICE, CONF_MAC, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_comports as mock_comports_fx,
    mock_device as mock_device_fx,
    mock_device_comm_error as mock_device_comm_error_fx,
    mock_device_no_open as mock_device_no_open_fx,
    mock_device_timeout as mock_device_timeout_fx,
)
from .const import DEVICE_NAME, DISCOVERY_INFO, METER_LIST

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def flow_usb(
    hass: HomeAssistant = Depends(hass_fixture),
    _ports: list = Depends(mock_comports_fx),
    _device: AsyncMock = Depends(mock_device_fx),
) -> None:
    """Test usb flow connection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USB}, data=DISCOVERY_INFO
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(bool(result.get("errors"))).to_be(False)
    expect(result.get("step_id")).to_equal("meters")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_MAC: [METER_LIST.meter_mac_ids[0].hex()]}
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)


@test
async def flow_usb_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    _ports: list = Depends(mock_comports_fx),
    _device: AsyncMock = Depends(mock_device_no_open_fx),
) -> None:
    """Test usb flow connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USB}, data=DISCOVERY_INFO
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("cannot_connect")


@test
async def flow_usb_timeout_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    _ports: list = Depends(mock_comports_fx),
    _device: AsyncMock = Depends(mock_device_timeout_fx),
) -> None:
    """Test usb flow connection timeout."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USB}, data=DISCOVERY_INFO
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("timeout_connect")


@test
async def flow_usb_comm_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _ports: list = Depends(mock_comports_fx),
    _device: AsyncMock = Depends(mock_device_comm_error_fx),
) -> None:
    """Test usb flow connection failure to communicate."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USB}, data=DISCOVERY_INFO
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("cannot_connect")


@test
async def flow_user(
    hass: HomeAssistant = Depends(hass_fixture),
    _ports: list = Depends(mock_comports_fx),
    _device: AsyncMock = Depends(mock_device_fx),
) -> None:
    """Test user flow connection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(bool(result.get("errors"))).to_be(False)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_DEVICE: DEVICE_NAME}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(bool(result.get("errors"))).to_be(False)
    expect(result.get("step_id")).to_equal("meters")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_MAC: [METER_LIST.meter_mac_ids[0].hex()]}
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)


@test
async def flow_user_no_available_devices(
    hass: HomeAssistant = Depends(hass_fixture),
    _ports: list = Depends(mock_comports_fx),
) -> None:
    """Test user flow with no available devices."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DEVICE: DISCOVERY_INFO.device},
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("no_devices_found")


@test
async def flow_user_in_progress(
    hass: HomeAssistant = Depends(hass_fixture),
    _ports: list = Depends(mock_comports_fx),
) -> None:
    """Test user flow with an in-progress flow blocks a second."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(bool(result.get("errors"))).to_be(False)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_in_progress")


@test
async def flow_user_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    _ports: list = Depends(mock_comports_fx),
    _device: AsyncMock = Depends(mock_device_no_open_fx),
) -> None:
    """Test user flow connection failure."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data={CONF_DEVICE: DEVICE_NAME},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({CONF_DEVICE: "cannot_connect"})


@test
async def flow_user_timeout_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    _ports: list = Depends(mock_comports_fx),
    _device: AsyncMock = Depends(mock_device_timeout_fx),
) -> None:
    """Test user flow connection failure due to timeout."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data={CONF_DEVICE: DEVICE_NAME},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({CONF_DEVICE: "timeout_connect"})


@test
async def flow_user_comm_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _ports: list = Depends(mock_comports_fx),
    _device: AsyncMock = Depends(mock_device_comm_error_fx),
) -> None:
    """Test user flow connection failure to communicate."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data={CONF_DEVICE: DEVICE_NAME},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({CONF_DEVICE: "cannot_connect"})
