"""Tests for the AsusWrt sensor."""

from datetime import timedelta
from typing import Any
from unittest.mock import MagicMock

from asusrouter import AsusRouterError
from asusrouter.modules.data import AsusData
from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components import device_tracker, sensor
from homeassistant.components.asuswrt.const import (
    CONF_INTERFACE,
    DOMAIN,
    SENSORS_BYTES,
    SENSORS_CONNECTED_DEVICE,
    SENSORS_CPU,
    SENSORS_LOAD_AVG,
    SENSORS_MEMORY,
    SENSORS_RATES,
    SENSORS_TEMPERATURES,
    SENSORS_TEMPERATURES_LEGACY,
    SENSORS_UPTIME,
)
from homeassistant.components.device_tracker import CONF_CONSIDER_HOME
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    CONF_PROTOCOL,
    STATE_HOME,
    STATE_NOT_HOME,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import slugify

from ._fixtures import (
    connect_http,
    connect_http_sens_detect,
    connect_http_sens_fail,
    connect_legacy,
    connect_legacy_sens_fail,
    make_async_get_data_side_effect,
    mock_available_temps,
    mock_devices_http,
    mock_devices_legacy,
)
from .common import (
    CONFIG_DATA_HTTP,
    CONFIG_DATA_TELNET,
    HOST,
    MOCK_MACS,
    ROUTER_MAC_ADDR,
    new_device,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)

SENSORS_DEFAULT = [*SENSORS_BYTES, *SENSORS_LOAD_AVG, *SENSORS_RATES]

SENSORS_ALL_LEGACY = [*SENSORS_DEFAULT, *SENSORS_TEMPERATURES_LEGACY]
SENSORS_ALL_HTTP = [
    *SENSORS_CPU,
    *SENSORS_DEFAULT,
    *SENSORS_MEMORY,
    *SENSORS_TEMPERATURES,
    *SENSORS_UPTIME,
]


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    return 0


@fixture
def create_device_registry_devices(
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Create device registry devices so the device tracker entities are enabled when added."""
    config_entry = MockConfigEntry(domain="something_else")
    config_entry.add_to_hass(hass)

    for idx, device in enumerate((MOCK_MACS[2], MOCK_MACS[3])):
        device_registry.async_get_or_create(
            name=f"Device {idx}",
            config_entry_id=config_entry.entry_id,
            connections={(dr.CONNECTION_NETWORK_MAC, dr.format_mac(device))},
        )


def _setup_entry(
    hass: HomeAssistant,
    config: dict[str, Any],
    sensors: list[str],
    unique_id: str | None = None,
) -> tuple[MockConfigEntry, str]:
    """Create mock config entry with enabled sensors."""
    entity_reg = er.async_get(hass)

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=config,
        options={CONF_CONSIDER_HOME: 60},
        unique_id=unique_id,
    )
    config_entry.add_to_hass(hass)

    obj_prefix = slugify(HOST)
    sensor_prefix = f"{sensor.DOMAIN}.{obj_prefix}"
    unique_id_prefix = slugify(unique_id or config_entry.entry_id)

    for sensor_key in sensors:
        sensor_id = slugify(sensor_key)
        entity_reg.async_get_or_create(
            sensor.DOMAIN,
            DOMAIN,
            f"{unique_id_prefix}_{sensor_id}",
            suggested_object_id=f"{obj_prefix}_{sensor_id}",
            config_entry=config_entry,
            disabled_by=None,
        )

    # Pre-register the devices_connected sensor with a predictable object_id
    # because translation strings may not be loaded in the test environment.
    connected_key = slugify(SENSORS_CONNECTED_DEVICE[0])
    entity_reg.async_get_or_create(
        sensor.DOMAIN,
        DOMAIN,
        f"{unique_id_prefix}_{connected_key}",
        suggested_object_id=f"{obj_prefix}_devices_connected",
        config_entry=config_entry,
        disabled_by=None,
    )

    return config_entry, sensor_prefix


async def _test_sensors(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_devices: dict,
    config: dict[str, Any],
    entry_unique_id: str | None,
) -> None:
    """Test creating AsusWRT default sensors and tracker."""
    config_entry, sensor_prefix = _setup_entry(
        hass, config, SENSORS_DEFAULT, entry_unique_id
    )

    entity_reg = er.async_get(hass)
    for mac, name in {
        MOCK_MACS[0]: "test",
        dr.format_mac(MOCK_MACS[1]): "testtwo",
        MOCK_MACS[1]: "testremove",
    }.items():
        entity_reg.async_get_or_create(
            device_tracker.DOMAIN,
            DOMAIN,
            mac,
            suggested_object_id=name,
            config_entry=config_entry,
            disabled_by=None,
        )

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(hass.states.get(f"{device_tracker.DOMAIN}.test").state).to_equal(STATE_HOME)
    expect(hass.states.get(f"{device_tracker.DOMAIN}.testtwo").state).to_equal(
        STATE_HOME
    )
    expect(hass.states.get(f"{sensor_prefix}_sensor_rx_rates").state).to_equal("160.0")
    expect(hass.states.get(f"{sensor_prefix}_sensor_rx_bytes").state).to_equal("60.0")
    expect(hass.states.get(f"{sensor_prefix}_sensor_tx_rates").state).to_equal("80.0")
    expect(hass.states.get(f"{sensor_prefix}_sensor_tx_bytes").state).to_equal("50.0")
    expect(hass.states.get(f"{sensor_prefix}_devices_connected").state).to_equal("2")
    expect(hass.states.get(f"{sensor_prefix}_sensor_load_avg1").state).to_equal("1.1")
    expect(hass.states.get(f"{sensor_prefix}_sensor_load_avg5").state).to_equal("1.2")
    expect(hass.states.get(f"{sensor_prefix}_sensor_load_avg15").state).to_equal("1.3")

    mock_devices.pop(MOCK_MACS[0])

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(hass.states.get(f"{device_tracker.DOMAIN}.test").state).to_equal(STATE_HOME)
    expect(hass.states.get(f"{device_tracker.DOMAIN}.testtwo").state).to_equal(
        STATE_HOME
    )
    expect(hass.states.get(f"{sensor_prefix}_devices_connected").state).to_equal("1")

    mock_devices[MOCK_MACS[2]] = new_device(
        config[CONF_PROTOCOL], MOCK_MACS[2], "192.168.1.4", "TestThree"
    )
    mock_devices[MOCK_MACS[3]] = new_device(
        config[CONF_PROTOCOL], MOCK_MACS[3], "192.168.1.5", None
    )

    hass.config_entries.async_update_entry(
        config_entry, options={CONF_CONSIDER_HOME: 0}
    )
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(hass.states.get(f"{device_tracker.DOMAIN}.test").state).to_equal(
        STATE_NOT_HOME
    )
    expect(hass.states.get(f"{device_tracker.DOMAIN}.testtwo").state).to_equal(
        STATE_HOME
    )
    expect(hass.states.get(f"{device_tracker.DOMAIN}.testthree").state).to_equal(
        STATE_HOME
    )
    expect(hass.states.get(f"{sensor_prefix}_devices_connected").state).to_equal("3")


@test.cases(
    test.case("no_unique_id", entry_unique_id=None),
    test.case("with_mac", entry_unique_id=ROUTER_MAC_ADDR),
)
async def sensors_legacy(
    entry_unique_id: str | None,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    mock_devices: dict = Depends(mock_devices_legacy),
    _connect: MagicMock = Depends(connect_legacy),
    _devices_registered: None = Depends(create_device_registry_devices),
) -> None:
    """Test creating AsusWRT default sensors and tracker with legacy protocol."""
    await _test_sensors(
        hass, freezer, mock_devices, CONFIG_DATA_TELNET, entry_unique_id
    )


@test.cases(
    test.case("no_unique_id", entry_unique_id=None),
    test.case("with_mac", entry_unique_id=ROUTER_MAC_ADDR),
)
async def sensors_http(
    entry_unique_id: str | None,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    mock_devices: dict = Depends(mock_devices_http),
    _connect: MagicMock = Depends(connect_http),
    _devices_registered: None = Depends(create_device_registry_devices),
) -> None:
    """Test creating AsusWRT default sensors and tracker with http protocol."""
    await _test_sensors(
        hass, freezer, mock_devices, CONFIG_DATA_HTTP, entry_unique_id
    )


async def _test_loadavg_sensors(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, config: dict[str, Any]
) -> None:
    """Test creating an AsusWRT load average sensors."""
    config_entry, sensor_prefix = _setup_entry(hass, config, SENSORS_LOAD_AVG)
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(hass.states.get(f"{sensor_prefix}_sensor_load_avg1").state).to_equal("1.1")
    expect(hass.states.get(f"{sensor_prefix}_sensor_load_avg5").state).to_equal("1.2")
    expect(hass.states.get(f"{sensor_prefix}_sensor_load_avg15").state).to_equal("1.3")


@test
async def loadavg_sensors_legacy(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    _connect: MagicMock = Depends(connect_legacy),
) -> None:
    """Test creating an AsusWRT load average sensors."""
    await _test_loadavg_sensors(hass, freezer, CONFIG_DATA_TELNET)


@test
async def loadavg_sensors_http(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    _connect: MagicMock = Depends(connect_http),
) -> None:
    """Test creating an AsusWRT load average sensors."""
    await _test_loadavg_sensors(hass, freezer, CONFIG_DATA_HTTP)


@test
async def loadavg_sensors_unaivalable_http(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    connect_http_mock: MagicMock = Depends(connect_http),
) -> None:
    """Test load average sensors no available using http."""
    config_entry, sensor_prefix = _setup_entry(hass, CONFIG_DATA_HTTP, SENSORS_LOAD_AVG)
    config_entry.add_to_hass(hass)

    connect_http_mock.return_value.async_get_data.side_effect = (
        make_async_get_data_side_effect([AsusData.SYSINFO])
    )

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(hass.states.get(f"{sensor_prefix}_sensor_load_avg1")).to_be_none()
    expect(hass.states.get(f"{sensor_prefix}_sensor_load_avg5")).to_be_none()
    expect(hass.states.get(f"{sensor_prefix}_sensor_load_avg15")).to_be_none()


@test
async def temperature_sensors_http_fail(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    connect_http_sens_fail_factory=Depends(connect_http_sens_fail),
) -> None:
    """Test fail creating AsusWRT temperature sensors."""
    _ = connect_http_sens_fail_factory([AsusData.TEMPERATURE])
    config_entry, sensor_prefix = _setup_entry(
        hass, CONFIG_DATA_HTTP, SENSORS_TEMPERATURES
    )
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(hass.states.get(f"{sensor_prefix}_2_4ghz")).to_be_none()
    expect(hass.states.get(f"{sensor_prefix}_5_0ghz")).to_be_none()
    expect(hass.states.get(f"{sensor_prefix}_cpu")).to_be_none()
    expect(hass.states.get(f"{sensor_prefix}_5_0ghz_2")).to_be_none()
    expect(hass.states.get(f"{sensor_prefix}_6_0ghz")).to_be_none()


async def _test_temperature_sensors(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config: dict[str, Any],
    sensors: list[str],
) -> str:
    """Test creating a AsusWRT temperature sensors."""
    config_entry, sensor_prefix = _setup_entry(hass, config, sensors)
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    return sensor_prefix


@test
async def temperature_sensors_legacy(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    _connect: MagicMock = Depends(connect_legacy),
) -> None:
    """Test creating a AsusWRT temperature sensors."""
    sensor_prefix = await _test_temperature_sensors(
        hass, freezer, CONFIG_DATA_TELNET, SENSORS_TEMPERATURES_LEGACY
    )
    expect(hass.states.get(f"{sensor_prefix}_2_4ghz").state).to_equal("40.2")
    expect(hass.states.get(f"{sensor_prefix}_cpu").state).to_equal("71.2")
    expect(hass.states.get(f"{sensor_prefix}_5_0ghz")).to_be_none()


@test
async def temperature_sensors_http(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    _connect: MagicMock = Depends(connect_http),
) -> None:
    """Test creating a AsusWRT temperature sensors."""
    sensor_prefix = await _test_temperature_sensors(
        hass, freezer, CONFIG_DATA_HTTP, SENSORS_TEMPERATURES
    )
    expect(hass.states.get(f"{sensor_prefix}_2_4ghz").state).to_equal("40.2")
    expect(hass.states.get(f"{sensor_prefix}_cpu").state).to_equal("71.2")
    expect(hass.states.get(f"{sensor_prefix}_5_0ghz_2").state).to_equal("40.3")
    expect(hass.states.get(f"{sensor_prefix}_6_0ghz").state).to_equal("40.4")
    expect(hass.states.get(f"{sensor_prefix}_5_0ghz")).to_be_none()


@test
async def cpu_sensors_http_fail(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    connect_http_sens_fail_factory=Depends(connect_http_sens_fail),
) -> None:
    """Test fail creating AsusWRT cpu sensors."""
    _ = connect_http_sens_fail_factory([AsusData.CPU])
    config_entry, sensor_prefix = _setup_entry(hass, CONFIG_DATA_HTTP, SENSORS_CPU)
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(hass.states.get(f"{sensor_prefix}_cpu1_usage")).to_be_none()
    expect(hass.states.get(f"{sensor_prefix}_cpu2_usage")).to_be_none()
    expect(hass.states.get(f"{sensor_prefix}_cpu3_usage")).to_be_none()
    expect(hass.states.get(f"{sensor_prefix}_cpu4_usage")).to_be_none()
    expect(hass.states.get(f"{sensor_prefix}_cpu5_usage")).to_be_none()
    expect(hass.states.get(f"{sensor_prefix}_cpu6_usage")).to_be_none()
    expect(hass.states.get(f"{sensor_prefix}_cpu7_usage")).to_be_none()
    expect(hass.states.get(f"{sensor_prefix}_cpu8_usage")).to_be_none()
    expect(hass.states.get(f"{sensor_prefix}_cpu_total_usage")).to_be_none()


@test
async def cpu_sensors_http(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    _connect: MagicMock = Depends(connect_http),
    _detect: MagicMock = Depends(connect_http_sens_detect),
) -> None:
    """Test creating AsusWRT cpu sensors."""
    config_entry, sensor_prefix = _setup_entry(hass, CONFIG_DATA_HTTP, SENSORS_CPU)
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(hass.states.get(f"{sensor_prefix}_cpu1_usage").state).to_equal("0.1")
    expect(hass.states.get(f"{sensor_prefix}_cpu2_usage").state).to_equal("0.2")
    expect(hass.states.get(f"{sensor_prefix}_cpu3_usage").state).to_equal("0.3")
    expect(hass.states.get(f"{sensor_prefix}_cpu4_usage").state).to_equal("0.4")
    expect(hass.states.get(f"{sensor_prefix}_cpu5_usage").state).to_equal("0.5")
    expect(hass.states.get(f"{sensor_prefix}_cpu6_usage").state).to_equal("0.6")
    expect(hass.states.get(f"{sensor_prefix}_cpu7_usage").state).to_equal("0.7")
    expect(hass.states.get(f"{sensor_prefix}_cpu8_usage").state).to_equal("0.8")
    expect(hass.states.get(f"{sensor_prefix}_cpu_total_usage").state).to_equal("0.9")


@test
async def memory_sensors_http(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    _connect: MagicMock = Depends(connect_http),
) -> None:
    """Test creating AsusWRT memory sensors."""
    config_entry, sensor_prefix = _setup_entry(hass, CONFIG_DATA_HTTP, SENSORS_MEMORY)
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(hass.states.get(f"{sensor_prefix}_mem_usage_perc").state).to_equal("52.4")
    expect(hass.states.get(f"{sensor_prefix}_mem_free").state).to_equal("384.0")
    expect(hass.states.get(f"{sensor_prefix}_mem_used").state).to_equal("640.0")


@test
async def uptime_sensors_http(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    _connect: MagicMock = Depends(connect_http),
) -> None:
    """Test creating AsusWRT uptime sensors."""
    config_entry, sensor_prefix = _setup_entry(hass, CONFIG_DATA_HTTP, SENSORS_UPTIME)
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(hass.states.get(f"{sensor_prefix}_sensor_last_boot").state).to_equal(
        "2024-08-02T00:47:00+00:00"
    )
    expect(hass.states.get(f"{sensor_prefix}_sensor_uptime").state).to_equal("1625927")


@test.cases(
    test.case("oserror", side_effect=OSError),
    test.case("none", side_effect=None),
)
async def connect_fail_legacy(
    side_effect: Any,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    connect_legacy_mock: MagicMock = Depends(connect_legacy),
) -> None:
    """Test AsusWRT connect fail."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_DATA_TELNET,
    )
    config_entry.add_to_hass(hass)

    connect_legacy_mock.return_value.connection.async_connect.side_effect = side_effect
    connect_legacy_mock.return_value.is_connected = False

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.cases(
    test.case("asusrouter_error", side_effect=AsusRouterError),
    test.case("none", side_effect=None),
)
async def connect_fail_http(
    side_effect: Any,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    connect_http_mock: MagicMock = Depends(connect_http),
) -> None:
    """Test AsusWRT connect fail."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_DATA_HTTP,
    )
    config_entry.add_to_hass(hass)

    connect_http_mock.return_value.async_connect.side_effect = side_effect
    connect_http_mock.return_value.connected = False

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


async def _test_sensors_polling_fails(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config: dict[str, Any],
    sensors: list[str],
) -> None:
    """Test AsusWRT sensors are unavailable when polling fails."""
    config_entry, sensor_prefix = _setup_entry(hass, config, sensors)
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    for sensor_name in sensors:
        expect(
            hass.states.get(f"{sensor_prefix}_{slugify(sensor_name)}").state
        ).to_equal(STATE_UNAVAILABLE)
    expect(hass.states.get(f"{sensor_prefix}_devices_connected").state).to_equal("0")


@test
async def sensors_polling_fails_legacy(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    _connect_fail: MagicMock = Depends(connect_legacy_sens_fail),
) -> None:
    """Test AsusWRT sensors are unavailable when polling fails."""
    await _test_sensors_polling_fails(
        hass, freezer, CONFIG_DATA_TELNET, SENSORS_ALL_LEGACY
    )


@test
async def sensors_polling_fails_http(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    connect_http_sens_fail_factory=Depends(connect_http_sens_fail),
    _detect: MagicMock = Depends(connect_http_sens_detect),
) -> None:
    """Test AsusWRT sensors are unavailable when polling fails."""
    fail_types = [
        AsusData.NETWORK,
        AsusData.CPU,
        AsusData.SYSINFO,
        AsusData.RAM,
        AsusData.TEMPERATURE,
        AsusData.BOOTTIME,
    ]
    _ = connect_http_sens_fail_factory(fail_types)
    await _test_sensors_polling_fails(hass, freezer, CONFIG_DATA_HTTP, SENSORS_ALL_HTTP)


@test
async def options_reload(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    connect_legacy_mock: MagicMock = Depends(connect_legacy),
) -> None:
    """Test AsusWRT integration is reload changing an options that require this."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_DATA_TELNET,
        unique_id=ROUTER_MAC_ADDR,
    )
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(
        connect_legacy_mock.return_value.connection.async_connect.call_count
    ).to_equal(1)

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    hass.config_entries.async_update_entry(
        config_entry, options={CONF_INTERFACE: "eth1"}
    )
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(
        connect_legacy_mock.return_value.connection.async_connect.call_count
    ).to_equal(2)


@test
async def unique_id_migration(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _connect: MagicMock = Depends(connect_legacy),
) -> None:
    """Test AsusWRT entities unique id format migration."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_DATA_TELNET,
        unique_id=ROUTER_MAC_ADDR,
    )
    config_entry.add_to_hass(hass)

    obj_entity_id = slugify(f"{HOST} Upload")
    entity_registry.async_get_or_create(
        sensor.DOMAIN,
        DOMAIN,
        f"{DOMAIN} {ROUTER_MAC_ADDR} Upload",
        suggested_object_id=obj_entity_id,
        config_entry=config_entry,
        disabled_by=None,
    )

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    migr_entity = entity_registry.async_get(f"{sensor.DOMAIN}.{obj_entity_id}")
    expect(migr_entity).not_.to_be_none()
    expect(migr_entity.unique_id).to_equal(slugify(f"{ROUTER_MAC_ADDR}_sensor_tx_bytes"))


@test
async def decorator_errors(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    connect_legacy_mock: MagicMock = Depends(connect_legacy),
    mock_available_temps_list: list[bool] = Depends(mock_available_temps),
) -> None:
    """Test AsusWRT sensors are unavailable on decorator type check error."""
    sensors = SENSORS_ALL_LEGACY
    config_entry, sensor_prefix = _setup_entry(hass, CONFIG_DATA_TELNET, sensors)
    config_entry.add_to_hass(hass)

    mock_available_temps_list[1] = True
    connect_legacy_mock.return_value.async_get_bytes_total.return_value = None
    connect_legacy_mock.return_value.async_get_current_transfer_rates.return_value = None
    connect_legacy_mock.return_value.async_get_temperature.return_value = None
    connect_legacy_mock.return_value.async_get_loadavg.return_value = None

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    for sensor_name in sensors:
        sensor_state = hass.states.get(f"{sensor_prefix}_{slugify(sensor_name)}")
        expect(sensor_state).not_.to_be_none()
        expect(sensor_state.state).to_equal(STATE_UNAVAILABLE)
