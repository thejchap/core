"""Tryke fixtures for Motion Blinds tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import Mock, patch

from tryke import fixture

TEST_HOST = "1.2.3.4"
TEST_HOST_HA = "9.10.11.12"
TEST_MAC = "ab:bb:cc:dd:ee:ff"
TEST_DEVICE_LIST = {TEST_MAC: Mock()}

TEST_DISCOVERY_1 = {
    TEST_HOST: {
        "msgType": "GetDeviceListAck",
        "mac": TEST_MAC,
        "deviceType": "02000002",
        "ProtocolVersion": "0.9",
        "token": "12345A678B9CDEFG",
        "data": [
            {"mac": "abcdefghujkl", "deviceType": "02000002"},
            {"mac": "abcdefghujkl0001", "deviceType": "10000000"},
            {"mac": "abcdefghujkl0002", "deviceType": "10000000"},
        ],
    }
}

TEST_INTERFACES = [
    {"enabled": True, "default": True, "ipv4": [{"address": TEST_HOST_HA}]}
]


@fixture
def motion_blinds_connect() -> Generator[None]:
    """Mock Motionblinds connection and entry setup."""
    with (
        patch(
            "homeassistant.components.motion_blinds.gateway.MotionGateway.GetDeviceList",
            return_value=True,
        ),
        patch(
            "homeassistant.components.motion_blinds.gateway.MotionGateway.Update",
            return_value=True,
        ),
        patch(
            "homeassistant.components.motion_blinds.gateway.MotionGateway.Check_gateway_multicast",
            return_value=True,
        ),
        patch(
            "homeassistant.components.motion_blinds.gateway.MotionGateway.device_list",
            TEST_DEVICE_LIST,
        ),
        patch(
            "homeassistant.components.motion_blinds.gateway.MotionGateway.mac",
            TEST_MAC,
        ),
        patch(
            "homeassistant.components.motion_blinds.config_flow.MotionDiscovery.discover",
            return_value=TEST_DISCOVERY_1,
        ),
        patch(
            "homeassistant.components.motion_blinds.config_flow.MotionGateway.GetDeviceList",
            return_value=True,
        ),
        patch(
            "homeassistant.components.motion_blinds.config_flow.MotionGateway.available",
            True,
        ),
        patch(
            "homeassistant.components.motion_blinds.gateway.AsyncMotionMulticast.Start_listen",
            return_value=True,
        ),
        patch(
            "homeassistant.components.motion_blinds.gateway.AsyncMotionMulticast.Stop_listen",
            return_value=True,
        ),
        patch(
            "homeassistant.components.motion_blinds.gateway.network.async_get_adapters",
            return_value=TEST_INTERFACES,
        ),
        patch(
            "homeassistant.components.motion_blinds.async_setup_entry",
            return_value=True,
        ),
    ):
        yield
