"""Tryke fixtures for Sunricher DALI tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.sunricher_dali.const import CONF_SERIAL_NUMBER, DOMAIN
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)

from .conftest import DEVICE_DATA, GATEWAY_HOST, GATEWAY_PORT, GATEWAY_SERIAL

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SERIAL_NUMBER: GATEWAY_SERIAL,
            CONF_HOST: GATEWAY_HOST,
            CONF_PORT: GATEWAY_PORT,
            CONF_NAME: "Test Gateway",
            CONF_USERNAME: "gateway_user",
            CONF_PASSWORD: "gateway_pass",
        },
        unique_id=GATEWAY_SERIAL,
        title="Test Gateway",
    )


def _create_mock_device(device_data: dict[str, Any]) -> MagicMock:
    """Create a mock device from device data dict."""
    device = MagicMock()
    device.dev_id = device_data["dev_id"]
    device.unique_id = device_data["dev_id"]
    device.status = "online"
    device.dev_type = device_data["dev_type"]
    device.name = device_data["name"]
    device.model = device_data["model"]
    device.gw_sn = GATEWAY_SERIAL
    device.color_mode = device_data["color_mode"]
    device.address = device_data["address"]
    device.channel = device_data["channel"]
    device.dev_sn = device_data.get("dev_sn", f"DEVSN-{device_data['address']:04d}")
    device.area_name = device_data.get("area_name", "Test Area")
    device.area_id = device_data.get("area_id", "test_area")
    device.turn_on = MagicMock()
    device.turn_off = MagicMock()
    device.read_status = MagicMock()
    device.register_listener = MagicMock(return_value=lambda: None)
    return device


@fixture
def mock_devices() -> list[MagicMock]:
    """Return mocked Device objects."""
    devices = [_create_mock_device(data) for data in DEVICE_DATA]
    devices.append(_create_mock_device(DEVICE_DATA[0]))
    return devices


@fixture
def mock_gateway(
    devices: list[MagicMock] = Depends(mock_devices),
) -> Generator[MagicMock]:
    """Return a mocked DaliGateway."""
    with (
        patch(
            "homeassistant.components.sunricher_dali.DaliGateway", autospec=True
        ) as mock_gateway_class,
        patch(
            "homeassistant.components.sunricher_dali.config_flow.DaliGateway",
            new=mock_gateway_class,
        ),
    ):
        gateway = mock_gateway_class.return_value
        gateway.gw_sn = GATEWAY_SERIAL
        gateway.gw_ip = GATEWAY_HOST
        gateway.port = GATEWAY_PORT
        gateway.name = "Test Gateway"
        gateway.username = "gateway_user"
        gateway.passwd = "gateway_pass"
        gateway.connect = AsyncMock()
        gateway.disconnect = AsyncMock()
        gateway.discover_devices = AsyncMock(return_value=devices)
        gateway.discover_scenes = AsyncMock(return_value=[])
        yield gateway


@fixture
def mock_discovery(
    gateway: MagicMock = Depends(mock_gateway),
) -> Generator[MagicMock]:
    """Mock DaliGatewayDiscovery."""
    with patch(
        "homeassistant.components.sunricher_dali.config_flow.DaliGatewayDiscovery"
    ) as mock_discovery_class:
        discovery = mock_discovery_class.return_value
        discovery.discover_gateways = AsyncMock(return_value=[gateway])
        yield discovery


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.sunricher_dali.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock
