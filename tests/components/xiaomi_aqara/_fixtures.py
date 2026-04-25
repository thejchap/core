"""Tryke fixtures for Xiaomi Aqara tests."""

from collections.abc import Generator
from socket import gaierror
from unittest.mock import Mock, patch

from tryke import fixture

TEST_HOST = "1.2.3.4"
TEST_HOST_2 = "5.6.7.8"
TEST_KEY = "1234567890123456"
TEST_PORT = 1234
TEST_NAME = "Test_Aqara_Gateway"
TEST_SID = "abcdefghijkl"
TEST_PROTOCOL = "1.1.1"
TEST_MAC = "ab:cd:ef:gh:ij:kl"
TEST_ZEROCONF_NAME = "lumi-gateway-v3_miio12345678._miio._udp.local."


def get_mock_discovery(
    host_list,
    invalid_interface=False,
    invalid_key=False,
    invalid_host=False,
    invalid_mac=False,
):
    """Return a mock gateway info instance."""
    gateway_discovery = Mock()

    gateway_dict = {}
    for host in host_list:
        gateway = Mock()

        gateway.ip_adress = host
        gateway.port = TEST_PORT
        gateway.sid = TEST_SID
        gateway.proto = TEST_PROTOCOL
        gateway.connection_error = invalid_host
        gateway.mac_error = invalid_mac

        if invalid_key:
            gateway.write_to_hub = Mock(return_value=False)

        gateway_dict[host] = gateway

    gateway_discovery.gateways = gateway_dict

    if invalid_interface:
        gateway_discovery.discover_gateways = Mock(side_effect=gaierror)

    return gateway_discovery


@fixture
def xiaomi_aqara() -> Generator[None]:
    """Mock xiaomi_aqara discovery and entry setup."""
    mock_gateway_discovery = get_mock_discovery([TEST_HOST])

    with (
        patch(
            "homeassistant.components.xiaomi_aqara.config_flow.XiaomiGatewayDiscovery",
            return_value=mock_gateway_discovery,
        ),
        patch(
            "homeassistant.components.xiaomi_aqara.config_flow.XiaomiGateway",
            return_value=mock_gateway_discovery.gateways[TEST_HOST],
        ),
        patch(
            "homeassistant.components.xiaomi_aqara.async_setup_entry",
            return_value=True,
        ),
    ):
        yield
