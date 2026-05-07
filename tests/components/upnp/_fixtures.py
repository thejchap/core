"""Tryke fixtures for the UPnP integration."""

from collections.abc import Generator
from datetime import datetime
import socket
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

from async_upnp_client.aiohttp import AiohttpNotifyServer
from async_upnp_client.client import UpnpDevice
from async_upnp_client.profiles.igd import IgdDevice, IgdState
from tryke import fixture

from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_MANUFACTURER,
    ATTR_UPNP_MODEL_NAME,
    ATTR_UPNP_SERIAL,
)

from .conftest import TEST_DISCOVERY


@fixture
def silent_ssdp_scanner() -> Generator[None]:
    """Start SSDP component and get Scanner, prevent actual SSDP traffic."""
    with (
        patch("homeassistant.components.ssdp.Scanner._async_start_ssdp_listeners"),
        patch("homeassistant.components.ssdp.Scanner._async_stop_ssdp_listeners"),
        patch("homeassistant.components.ssdp.Scanner.async_scan"),
        patch(
            "homeassistant.components.ssdp.Server._async_start_upnp_servers",
        ),
        patch(
            "homeassistant.components.ssdp.Server._async_stop_upnp_servers",
        ),
    ):
        yield


@fixture
def mock_igd_device() -> Generator[IgdDevice]:
    """Mock async_upnp_client device."""
    mock_upnp_device = create_autospec(UpnpDevice, instance=True)
    mock_upnp_device.device_url = TEST_DISCOVERY.ssdp_location
    mock_upnp_device.serial_number = TEST_DISCOVERY.upnp[ATTR_UPNP_SERIAL]

    mock_igd_device_obj = create_autospec(IgdDevice)
    mock_igd_device_obj.device_type = TEST_DISCOVERY.ssdp_st
    mock_igd_device_obj.name = TEST_DISCOVERY.upnp[ATTR_UPNP_FRIENDLY_NAME]
    mock_igd_device_obj.manufacturer = TEST_DISCOVERY.upnp[ATTR_UPNP_MANUFACTURER]
    mock_igd_device_obj.model_name = TEST_DISCOVERY.upnp[ATTR_UPNP_MODEL_NAME]
    mock_igd_device_obj.udn = TEST_DISCOVERY.ssdp_udn
    mock_igd_device_obj.device = mock_upnp_device

    mock_igd_device_obj.async_get_traffic_and_status_data.return_value = IgdState(
        timestamp=datetime.now(),
        bytes_received=0,
        bytes_sent=0,
        packets_received=0,
        packets_sent=0,
        connection_status="Connected",
        last_connection_error="",
        uptime=10,
        external_ip_address="8.9.10.11",
        kibibytes_per_sec_received=None,
        kibibytes_per_sec_sent=None,
        packets_per_sec_received=None,
        packets_per_sec_sent=None,
        port_mapping_number_of_entries=0,
    )

    mock_igd_device_obj.async_subscribe_services = AsyncMock()

    mock_notify_server = create_autospec(AiohttpNotifyServer)
    mock_notify_server.event_handler = MagicMock()

    with (
        patch(
            "homeassistant.components.upnp.device.async_get_local_ip",
            return_value=(socket.AF_INET, "127.0.0.1"),
        ),
        patch(
            "homeassistant.components.upnp.device.IgdDevice.__new__",
            return_value=mock_igd_device_obj,
        ),
        patch(
            "homeassistant.components.upnp.device.AiohttpNotifyServer.__new__",
            return_value=mock_notify_server,
        ),
    ):
        yield mock_igd_device_obj
