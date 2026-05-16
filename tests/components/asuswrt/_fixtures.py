"""Tryke fixtures for the AsusWrt integration."""

from collections.abc import Callable, Generator
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from aioasuswrt.asuswrt import AsusWrt as AsusWrtLegacy
from aioasuswrt.connection import TelnetConnection
from asusrouter import AsusRouter, AsusRouterError
from asusrouter.modules.data import AsusData
from asusrouter.modules.identity import AsusDevice
from tryke import Depends, fixture

from .common import (
    ASUSWRT_BASE,
    HOST,
    MOCK_MACS,
    PROTOCOL_HTTP,
    PROTOCOL_SSH,
    ROUTER_MAC_ADDR,
    new_device,
)

ASUSWRT_HTTP_LIB = f"{ASUSWRT_BASE}.bridge.AsusRouter"
ASUSWRT_LEGACY_LIB = f"{ASUSWRT_BASE}.bridge.AsusWrtLegacy"

MOCK_BYTES_TOTAL = 60000000000, 50000000000
MOCK_BYTES_TOTAL_HTTP = dict(enumerate(MOCK_BYTES_TOTAL))
MOCK_CPU_USAGE = {
    "cpu1_usage": 0.1,
    "cpu2_usage": 0.2,
    "cpu3_usage": 0.3,
    "cpu4_usage": 0.4,
    "cpu5_usage": 0.5,
    "cpu6_usage": 0.6,
    "cpu7_usage": 0.7,
    "cpu8_usage": 0.8,
    "cpu_total_usage": 0.9,
}
MOCK_CURRENT_TRANSFER_RATES = 20000000, 10000000
MOCK_CURRENT_TRANSFER_RATES_HTTP = dict(enumerate(MOCK_CURRENT_TRANSFER_RATES))
MOCK_CURRENT_NETWORK = {
    "sensor_rx_rates": MOCK_CURRENT_TRANSFER_RATES[0] * 8,
    "sensor_tx_rates": MOCK_CURRENT_TRANSFER_RATES[1] * 8,
    "sensor_rx_bytes": MOCK_BYTES_TOTAL[0],
    "sensor_tx_bytes": MOCK_BYTES_TOTAL[1],
}
MOCK_LOAD_AVG_HTTP = {"load_avg_1": 1.1, "load_avg_5": 1.2, "load_avg_15": 1.3}
MOCK_LOAD_AVG = list(MOCK_LOAD_AVG_HTTP.values())
MOCK_SYSINFO = {
    "sensor_load_avg1": MOCK_LOAD_AVG[0],
    "sensor_load_avg5": MOCK_LOAD_AVG[1],
    "sensor_load_avg15": MOCK_LOAD_AVG[2],
}
MOCK_MEMORY_USAGE = {
    "mem_usage_perc": 52.4,
    "mem_total": 1048576,
    "mem_free": 393216,
    "mem_used": 655360,
}
MOCK_TEMPERATURES = {"2.4GHz": 40.2, "5.0GHz": 0, "CPU": 71.2}
MOCK_TEMPERATURES_HTTP = {**MOCK_TEMPERATURES, "5.0GHz_2": 40.3, "6.0GHz": 40.4}
MOCK_UPTIME = {"last_boot": "2024-08-02T00:47:00+00:00", "uptime": 1625927}
MOCK_BOOTTIME = {
    "sensor_last_boot": datetime.fromisoformat(MOCK_UPTIME["last_boot"]),
    "sensor_uptime": MOCK_UPTIME["uptime"],
}


def make_async_get_data_side_effect(fail_types=None):
    """Return a side effect for async_get_data that fails for specified AsusData types."""
    fail_types = set(fail_types or [])

    def side_effect(datatype, *args, **kwargs):
        if datatype in fail_types:
            raise AsusRouterError(f"{datatype} unavailable")
        return {}

    return side_effect


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


@fixture
def connect_legacy_sens_fail(
    connect_legacy: MagicMock = Depends(connect_legacy),
) -> MagicMock:
    """Mock a successful connection using legacy library with sensors fail."""
    connect_legacy.return_value.async_get_nvram.side_effect = OSError
    connect_legacy.return_value.async_get_connected_devices.side_effect = OSError
    connect_legacy.return_value.async_get_bytes_total.side_effect = OSError
    connect_legacy.return_value.async_get_current_transfer_rates.side_effect = OSError
    connect_legacy.return_value.async_get_loadavg.side_effect = OSError
    connect_legacy.return_value.async_get_temperature.side_effect = OSError
    connect_legacy.return_value.async_find_temperature_commands.return_value = [
        True,
        True,
        True,
    ]
    return connect_legacy


@fixture
def mock_devices_http() -> dict:
    """Mock a list of AsusRouter client devices for HTTP backend."""
    return {
        MOCK_MACS[0]: new_device(
            PROTOCOL_HTTP, MOCK_MACS[0], "192.168.1.2", "Test", "node1"
        ),
        MOCK_MACS[1]: new_device(
            PROTOCOL_HTTP, MOCK_MACS[1], "192.168.1.3", "TestTwo", "node2"
        ),
    }


@fixture
def connect_http(
    mock_devices_http: dict = Depends(mock_devices_http),
) -> Generator[MagicMock]:
    """Mock a successful connection with http library."""
    with patch(ASUSWRT_HTTP_LIB, spec_set=AsusRouter) as service_mock:
        instance = service_mock.return_value

        instance.connected = True
        instance.webpanel = f"http://{HOST}:80"

        instance.async_get_identity.return_value = AsusDevice(
            mac=ROUTER_MAC_ADDR,
            model="FAKE_MODEL",
            firmware="FAKE_FIRMWARE",
        )

        instance.async_get_data.side_effect = lambda datatype, *args, **kwargs: {
            AsusData.CLIENTS: mock_devices_http,
            AsusData.NETWORK: MOCK_CURRENT_NETWORK,
            AsusData.SYSINFO: MOCK_SYSINFO,
            AsusData.TEMPERATURE: {
                k: v for k, v in MOCK_TEMPERATURES_HTTP.items() if k != "5.0GHz"
            },
            AsusData.CPU: MOCK_CPU_USAGE,
            AsusData.RAM: MOCK_MEMORY_USAGE,
            AsusData.BOOTTIME: MOCK_BOOTTIME,
        }[datatype]

        yield service_mock


@fixture
def connect_http_sens_fail(
    connect_http: MagicMock = Depends(connect_http),
) -> Callable[[list], MagicMock]:
    """Universal fixture to fail specified AsusData types."""

    def _set_fail_types(fail_types):
        connect_http.return_value.async_get_data.side_effect = (
            make_async_get_data_side_effect(fail_types)
        )
        return connect_http

    return _set_fail_types


@fixture
def connect_http_sens_detect() -> Generator[MagicMock]:
    """Mock a successful sensor detection using http library."""

    async def _get_sensors_side_effect(datatype):
        if datatype == AsusData.TEMPERATURE:
            return list(MOCK_TEMPERATURES_HTTP)
        if datatype == AsusData.CPU:
            return list(MOCK_CPU_USAGE)
        if datatype == AsusData.SYSINFO:
            return list(MOCK_SYSINFO)
        return []

    with patch(
        f"{ASUSWRT_BASE}.bridge.AsusWrtHttpBridge._get_sensors",
        side_effect=_get_sensors_side_effect,
    ) as mock_sens_detect:
        yield mock_sens_detect
