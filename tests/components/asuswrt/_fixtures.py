"""Tryke fixtures for the AsusWrt integration."""

from collections.abc import Generator
from unittest.mock import MagicMock, Mock, patch

from aioasuswrt.asuswrt import AsusWrt as AsusWrtLegacy
from aioasuswrt.connection import TelnetConnection
from tryke import Depends, fixture

from .common import ASUSWRT_BASE, MOCK_MACS, PROTOCOL_SSH, ROUTER_MAC_ADDR, new_device

ASUSWRT_LEGACY_LIB = f"{ASUSWRT_BASE}.bridge.AsusWrtLegacy"

MOCK_BYTES_TOTAL = 60000000000, 50000000000
MOCK_CURRENT_TRANSFER_RATES = 20000000, 10000000
MOCK_LOAD_AVG_HTTP = {"load_avg_1": 1.1, "load_avg_5": 1.2, "load_avg_15": 1.3}
MOCK_LOAD_AVG = list(MOCK_LOAD_AVG_HTTP.values())
MOCK_TEMPERATURES = {"2.4GHz": 40.2, "5.0GHz": 0, "CPU": 71.2}


@fixture
def patch_get_host() -> Generator:
    """Mock call to socket gethostbyname function.

    Patches the wrapper function ``_get_ip`` rather than the global
    ``socket.gethostbyname`` to avoid leaking into other modules.
    """
    with patch(
        f"{ASUSWRT_BASE}.config_flow._get_ip", return_value="192.168.1.1"
    ) as get_host_mock:
        yield get_host_mock


@fixture
def patch_is_file() -> Generator:
    """Mock call to os path.isfile function.

    Patches the wrapper ``_is_file`` rather than the global
    ``os.path.isfile`` (which would corrupt e.g. zoneinfo tzdata
    lookups via shared ``os.path``).
    """
    with patch(
        f"{ASUSWRT_BASE}.config_flow._is_file", return_value=True
    ) as is_file_mock:
        yield is_file_mock


@fixture
def mock_devices_legacy() -> dict:
    """Mock a list of devices."""
    return {
        MOCK_MACS[0]: new_device(PROTOCOL_SSH, MOCK_MACS[0], "192.168.1.2", "Test"),
        MOCK_MACS[1]: new_device(PROTOCOL_SSH, MOCK_MACS[1], "192.168.1.3", "TestTwo"),
    }


@fixture
def mock_available_temps() -> list[bool]:
    """Mock a list of available temperature sensors."""
    return [True, False, True]


@fixture
def connect_legacy(
    mock_devices_legacy: dict = Depends(mock_devices_legacy),
    mock_available_temps: list[bool] = Depends(mock_available_temps),
) -> Generator[MagicMock]:
    """Mock a successful connection with legacy library."""
    with patch(ASUSWRT_LEGACY_LIB, spec=AsusWrtLegacy) as service_mock:
        service_mock.return_value.connection = Mock(spec=TelnetConnection)
        service_mock.return_value.is_connected = True
        service_mock.return_value.async_get_nvram.return_value = {
            "label_mac": ROUTER_MAC_ADDR,
            "model": "abcd",
            "firmver": "efg",
            "buildno": "123",
        }
        service_mock.return_value.async_get_connected_devices.return_value = (
            mock_devices_legacy
        )
        service_mock.return_value.async_get_bytes_total.return_value = MOCK_BYTES_TOTAL
        service_mock.return_value.async_get_current_transfer_rates.return_value = (
            MOCK_CURRENT_TRANSFER_RATES
        )
        service_mock.return_value.async_get_loadavg.return_value = MOCK_LOAD_AVG
        service_mock.return_value.async_get_temperature.return_value = MOCK_TEMPERATURES
        service_mock.return_value.async_find_temperature_commands.return_value = (
            mock_available_temps
        )
        yield service_mock
