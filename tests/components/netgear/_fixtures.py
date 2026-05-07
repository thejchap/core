"""Tryke fixtures for the netgear integration."""

from collections.abc import Generator
from unittest.mock import Mock, patch

from tryke import fixture

ROUTER_INFOS = {
    "Description": "Netgear Smart Wizard 3.0, specification 1.6 version",
    "SignalStrength": "-4",
    "SmartAgentversion": "3.0",
    "FirewallVersion": "net-wall 2.0",
    "VPNVersion": None,
    "OthersoftwareVersion": "N/A",
    "Hardwareversion": "N/A",
    "Otherhardwareversion": "N/A",
    "FirstUseDate": "Sunday, 30 Sep 2007 01:10:03",
    "DeviceMode": "0",
    "ModelName": "RBR20",
    "SerialNumber": "5ER1AL0000001",
    "Firmwareversion": "V2.3.5.26",
    "DeviceName": "Desk",
    "DeviceNameUserSet": "true",
    "FirmwareDLmethod": "HTTPS",
    "FirmwareLastUpdate": "2019_10.5_18:42:58",
    "FirmwareLastChecked": "2020_5.3_1:33:0",
    "DeviceModeCapability": "0;1",
}


@fixture
def mock_service() -> Generator[Mock]:
    """Mock a successful Netgear service."""
    with (
        patch("homeassistant.components.netgear.async_setup_entry", return_value=True),
        patch("homeassistant.components.netgear.router.Netgear") as service_mock,
    ):
        service_mock.return_value.get_info = Mock(return_value=ROUTER_INFOS)
        service_mock.return_value.port = 80
        service_mock.return_value.ssl = False
        yield service_mock
