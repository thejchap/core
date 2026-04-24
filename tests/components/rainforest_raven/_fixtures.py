"""Tryke fixtures for Rainforest RAVEn config flow tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from aioraven.device import RAVEnConnectionError
from tryke import Depends, fixture

from homeassistant.components.usb import USBDevice

from . import create_mock_device
from .const import DISCOVERY_INFO


@fixture
def mock_device() -> Generator[AsyncMock]:
    """Mock a functioning RAVEn device."""
    device = create_mock_device()
    with patch(
        "homeassistant.components.rainforest_raven.config_flow.RAVEnSerialDevice",
        return_value=device,
    ):
        yield device


@fixture
def mock_device_no_open(device: AsyncMock = Depends(mock_device)) -> AsyncMock:
    """Mock a device which fails to open."""
    device.__aenter__.side_effect = RAVEnConnectionError
    device.open.side_effect = RAVEnConnectionError
    return device


@fixture
def mock_device_comm_error(device: AsyncMock = Depends(mock_device)) -> AsyncMock:
    """Mock a device which fails to read or parse raw data."""
    device.get_meter_list.side_effect = RAVEnConnectionError
    device.get_meter_info.side_effect = RAVEnConnectionError
    return device


@fixture
def mock_device_timeout(device: AsyncMock = Depends(mock_device)) -> AsyncMock:
    """Mock a device which times out when queried."""
    device.get_meter_list.side_effect = TimeoutError
    device.get_meter_info.side_effect = TimeoutError
    return device


@fixture
def mock_comports() -> Generator[list[USBDevice]]:
    """Mock serial port list."""
    port = USBDevice(
        device=DISCOVERY_INFO.device,
        vid=f"{int(DISCOVERY_INFO.vid, 16):04X}",
        pid=f"{int(DISCOVERY_INFO.pid, 16):04X}",
        serial_number=DISCOVERY_INFO.serial_number,
        manufacturer=DISCOVERY_INFO.manufacturer,
        description=DISCOVERY_INFO.description,
    )
    comports = [port]
    with patch(
        "homeassistant.components.rainforest_raven.config_flow.usb.async_scan_serial_ports",
        return_value=comports,
    ):
        yield comports
