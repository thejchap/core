"""Tests for the Bluetooth base scanner models."""

from datetime import timedelta
import time
from typing import Any
from unittest.mock import patch

# pylint: disable-next=no-name-in-module
from habluetooth.advertisement_tracker import TRACKER_BUFFERING_WOBBLE_SECONDS
from tryke import Depends, expect, fixture, test

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BaseHaRemoteScanner,
    HaBluetoothConnector,
    storage,
)
from homeassistant.components.bluetooth.const import (
    CONNECTABLE_FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS,
    FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS,
    SCANNER_WATCHDOG_INTERVAL,
    SCANNER_WATCHDOG_TIMEOUT,
    UNAVAILABLE_TRACK_SECONDS,
)
from homeassistant.components.bluetooth.manager import HomeAssistantBluetoothManager
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from homeassistant.util.json import json_loads

from . import (
    FakeRemoteScanner as FakeScanner,
    MockBleakClient,
    _get_manager,
    generate_advertisement_data,
    generate_ble_device,
    patch_bluetooth_time,
)
from ._fixtures import disable_new_discovery_flows as disable_new_discovery_flows_fixture

from tests.common import MockConfigEntry, async_fire_time_changed, async_load_fixture
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    enable_bluetooth as enable_bluetooth_fixture,
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case("name_none", name_2=None),
    test.case("name_w", name_2="w"),
)
async def remote_scanner(
    name_2: str | None,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _enable_bluetooth: None = Depends(enable_bluetooth_fixture),
) -> None:
    """Test the remote scanner base class merges advertisement_data."""
    manager = _get_manager()

    switchbot_device = generate_ble_device(
        "44:44:33:11:23:45",
        "wohand",
        {},
    )
    switchbot_device_adv = generate_advertisement_data(
        local_name="wohand",
        service_uuids=["050a021a-0000-1000-8000-00805f9b34fb"],
        service_data={"050a021a-0000-1000-8000-00805f9b34fb": b"\n\xff"},
        manufacturer_data={1: b"\x01"},
        rssi=-100,
    )
    switchbot_device_2 = generate_ble_device(
        "44:44:33:11:23:45",
        name_2,
        {},
    )
    switchbot_device_adv_2 = generate_advertisement_data(
        local_name=name_2,
        service_uuids=["00000001-0000-1000-8000-00805f9b34fb"],
        service_data={"00000001-0000-1000-8000-00805f9b34fb": b"\n\xff"},
        manufacturer_data={1: b"\x01", 2: b"\x02"},
        rssi=-100,
    )
    switchbot_device_3 = generate_ble_device(
        "44:44:33:11:23:45",
        "wohandlonger",
        {},
    )
    switchbot_device_adv_3 = generate_advertisement_data(
        local_name="wohandlonger",
        service_uuids=["00000001-0000-1000-8000-00805f9b34fb"],
        service_data={"00000001-0000-1000-8000-00805f9b34fb": b"\n\xff"},
        manufacturer_data={1: b"\x01", 2: b"\x02"},
        rssi=-100,
    )

    connector = (
        HaBluetoothConnector(MockBleakClient, "mock_bleak_client", lambda: False),
    )
    scanner = FakeScanner("esp32", "esp32", connector, True)
    unsetup = scanner.async_setup()
    cancel = manager.async_register_scanner(scanner)

    scanner.inject_advertisement(switchbot_device, switchbot_device_adv)

    data = scanner.discovered_devices_and_advertisement_data
    discovered_device, discovered_adv_data = data[switchbot_device.address]
    expect(discovered_device.address).to_equal(switchbot_device.address)
    expect(discovered_device.name).to_equal(switchbot_device.name)
    expect(discovered_adv_data.manufacturer_data).to_equal(
        switchbot_device_adv.manufacturer_data
    )
    expect(discovered_adv_data.service_data).to_equal(switchbot_device_adv.service_data)
    expect(discovered_adv_data.service_uuids).to_equal(
        switchbot_device_adv.service_uuids
    )
    scanner.inject_advertisement(switchbot_device_2, switchbot_device_adv_2)

    data = scanner.discovered_devices_and_advertisement_data
    discovered_device, discovered_adv_data = data[switchbot_device.address]
    expect(discovered_device.address).to_equal(switchbot_device.address)
    expect(discovered_device.name).to_equal(switchbot_device.name)
    expect(discovered_adv_data.manufacturer_data).to_equal({1: b"\x01", 2: b"\x02"})
    expect(discovered_adv_data.service_data).to_equal(
        {
            "050a021a-0000-1000-8000-00805f9b34fb": b"\n\xff",
            "00000001-0000-1000-8000-00805f9b34fb": b"\n\xff",
        }
    )
    expect(set(discovered_adv_data.service_uuids)).to_equal(
        {
            "050a021a-0000-1000-8000-00805f9b34fb",
            "00000001-0000-1000-8000-00805f9b34fb",
        }
    )

    # The longer name should be used
    scanner.inject_advertisement(switchbot_device_3, switchbot_device_adv_3)
    expect(discovered_device.name).to_equal(switchbot_device_3.name)

    # Inject the shorter name / None again to make
    # sure we always keep the longer name
    scanner.inject_advertisement(switchbot_device_2, switchbot_device_adv_2)
    expect(discovered_device.name).to_equal(switchbot_device_3.name)

    cancel()
    unsetup()


@test
async def remote_scanner_expires_connectable(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _enable_bluetooth: None = Depends(enable_bluetooth_fixture),
) -> None:
    """Test the remote scanner expires stale connectable data."""
    manager = _get_manager()

    switchbot_device = generate_ble_device(
        "44:44:33:11:23:45",
        "wohand",
        {},
    )
    switchbot_device_adv = generate_advertisement_data(
        local_name="wohand",
        service_uuids=[],
        manufacturer_data={1: b"\x01"},
        rssi=-100,
    )

    connector = (
        HaBluetoothConnector(MockBleakClient, "mock_bleak_client", lambda: False),
    )
    scanner = FakeScanner("esp32", "esp32", connector, True)
    unsetup = scanner.async_setup()
    cancel = manager.async_register_scanner(scanner)

    start_time_monotonic = time.monotonic()
    scanner.inject_advertisement(switchbot_device, switchbot_device_adv)

    devices = scanner.discovered_devices
    expect(len(scanner.discovered_devices)).to_equal(1)
    expect(len(scanner.discovered_devices_and_advertisement_data)).to_equal(1)
    expect(devices[0].name).to_equal("wohand")

    expire_monotonic = (
        start_time_monotonic
        + CONNECTABLE_FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS
        + 1
    )
    expire_utc = dt_util.utcnow() + timedelta(
        seconds=CONNECTABLE_FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS + 1
    )
    with patch_bluetooth_time(expire_monotonic):
        async_fire_time_changed(hass, expire_utc)
        await hass.async_block_till_done()

    devices = scanner.discovered_devices
    expect(len(scanner.discovered_devices)).to_equal(0)
    expect(len(scanner.discovered_devices_and_advertisement_data)).to_equal(0)

    cancel()
    unsetup()


@test
async def remote_scanner_expires_non_connectable(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _enable_bluetooth: None = Depends(enable_bluetooth_fixture),
) -> None:
    """Test the remote scanner expires stale non connectable data."""
    manager = _get_manager()

    switchbot_device = generate_ble_device(
        "44:44:33:11:23:45",
        "wohand",
        {},
    )
    switchbot_device_adv = generate_advertisement_data(
        local_name="wohand",
        service_uuids=[],
        manufacturer_data={1: b"\x01"},
        rssi=-100,
    )

    connector = (
        HaBluetoothConnector(MockBleakClient, "mock_bleak_client", lambda: False),
    )
    scanner = FakeScanner("esp32", "esp32", connector, True)
    unsetup = scanner.async_setup()
    cancel = manager.async_register_scanner(scanner)

    start_time_monotonic = time.monotonic()
    scanner.inject_advertisement(switchbot_device, switchbot_device_adv)

    devices = scanner.discovered_devices
    expect(len(scanner.discovered_devices)).to_equal(1)
    expect(len(scanner.discovered_devices_and_advertisement_data)).to_equal(1)
    expect(devices[0].name).to_equal("wohand")

    expect(
        FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS
        > CONNECTABLE_FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS
    ).to_be(True)

    # The connectable timeout is used for all devices
    # as the manager takes care of availability and the scanner
    # if only concerned about making a connection
    expire_monotonic = (
        start_time_monotonic
        + CONNECTABLE_FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS
        + 1
    )
    expire_utc = dt_util.utcnow() + timedelta(
        seconds=CONNECTABLE_FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS + 1
    )
    with patch_bluetooth_time(expire_monotonic):
        async_fire_time_changed(hass, expire_utc)
        await hass.async_block_till_done()

    expect(len(scanner.discovered_devices)).to_equal(0)
    expect(len(scanner.discovered_devices_and_advertisement_data)).to_equal(0)

    expire_monotonic = (
        start_time_monotonic + FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS + 1
    )
    expire_utc = dt_util.utcnow() + timedelta(
        seconds=FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS + 1
    )
    with patch_bluetooth_time(expire_monotonic):
        async_fire_time_changed(hass, expire_utc)
        await hass.async_block_till_done()

    expect(len(scanner.discovered_devices)).to_equal(0)
    expect(len(scanner.discovered_devices_and_advertisement_data)).to_equal(0)

    cancel()
    unsetup()


@test
async def base_scanner_connecting_behavior(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _enable_bluetooth: None = Depends(enable_bluetooth_fixture),
) -> None:
    """Test that the default behavior is to mark the scanner as not scanning when connecting."""
    manager = _get_manager()

    switchbot_device = generate_ble_device(
        "44:44:33:11:23:45",
        "wohand",
        {},
    )
    switchbot_device_adv = generate_advertisement_data(
        local_name="wohand",
        service_uuids=[],
        manufacturer_data={1: b"\x01"},
        rssi=-100,
    )

    connector = (
        HaBluetoothConnector(MockBleakClient, "mock_bleak_client", lambda: False),
    )
    scanner = FakeScanner("esp32", "esp32", connector, True)
    unsetup = scanner.async_setup()
    cancel = manager.async_register_scanner(scanner)

    with scanner.connecting():
        expect(scanner.scanning).to_be(False)

        # We should still accept new advertisements while connecting
        # since advertisements are delivered asynchronously and
        # we don't want to miss any even when we are willing to
        # accept advertisements from another scanner in the brief window
        # between when we start connecting and when we stop scanning
        scanner.inject_advertisement(switchbot_device, switchbot_device_adv)

    devices = scanner.discovered_devices
    expect(len(scanner.discovered_devices)).to_equal(1)
    expect(len(scanner.discovered_devices_and_advertisement_data)).to_equal(1)
    expect(devices[0].name).to_equal("wohand")

    cancel()
    unsetup()


@test
async def restore_history_remote_adapter(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    _disable_new_discovery_flows: Any = Depends(disable_new_discovery_flows_fixture),
) -> None:
    """Test we can restore history for a remote adapter."""
    data = hass_storage[storage.REMOTE_SCANNER_STORAGE_KEY] = json_loads(
        await async_load_fixture(hass, "bluetooth.remote_scanners", bluetooth.DOMAIN)
    )
    now = time.time()
    timestamps = data["data"]["atom-bluetooth-proxy-ceaac4"][
        "discovered_device_timestamps"
    ]
    for address in timestamps:
        if address != "E3:A5:63:3E:5E:23":
            timestamps[address] = now

    with (
        patch(
            "bluetooth_adapters.systems.linux.LinuxAdapters.history",
            {},
        ),
        patch(
            "bluetooth_adapters.systems.linux.LinuxAdapters.refresh",
        ),
    ):
        expect(await async_setup_component(hass, bluetooth.DOMAIN, {})).to_be(True)
        await hass.async_block_till_done()

    connector = (
        HaBluetoothConnector(MockBleakClient, "mock_bleak_client", lambda: False),
    )
    scanner = BaseHaRemoteScanner(
        "atom-bluetooth-proxy-ceaac4",
        "atom-bluetooth-proxy-ceaac4",
        connector,
        True,
    )
    unsetup = scanner.async_setup()
    cancel = _get_manager().async_register_scanner(scanner)

    expect(
        "EB:0B:36:35:6F:A4" in scanner.discovered_devices_and_advertisement_data
    ).to_be(True)
    expect(
        "E3:A5:63:3E:5E:23" in scanner.discovered_devices_and_advertisement_data
    ).to_be(False)
    cancel()
    unsetup()

    scanner = BaseHaRemoteScanner(
        "atom-bluetooth-proxy-ceaac4",
        "atom-bluetooth-proxy-ceaac4",
        connector,
        True,
    )
    unsetup = scanner.async_setup()
    cancel = _get_manager().async_register_scanner(scanner)
    expect(
        "EB:0B:36:35:6F:A4" in scanner.discovered_devices_and_advertisement_data
    ).to_be(True)
    expect(
        "E3:A5:63:3E:5E:23" in scanner.discovered_devices_and_advertisement_data
    ).to_be(False)

    cancel()
    unsetup()


@test
async def device_with_ten_minute_advertising_interval(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _enable_bluetooth: None = Depends(enable_bluetooth_fixture),
) -> None:
    """Test a device with a 10 minute advertising interval."""
    manager = _get_manager()

    bparasite_device = generate_ble_device(
        "44:44:33:11:23:45",
        "bparasite",
        {},
    )
    bparasite_device_adv = generate_advertisement_data(
        local_name="bparasite",
        service_uuids=[],
        manufacturer_data={1: b"\x01"},
        rssi=-100,
    )

    connector = (
        HaBluetoothConnector(MockBleakClient, "mock_bleak_client", lambda: False),
    )
    scanner = FakeScanner("esp32", "esp32", connector, True)
    unsetup = scanner.async_setup()
    cancel = manager.async_register_scanner(scanner)

    monotonic_now = time.monotonic()
    new_time = monotonic_now
    bparasite_device_went_unavailable = False

    @callback
    def _bparasite_device_unavailable_callback(_address: str) -> None:
        """Barasite device unavailable callback."""
        nonlocal bparasite_device_went_unavailable
        bparasite_device_went_unavailable = True

    advertising_interval = 60 * 10

    bparasite_device_unavailable_cancel = bluetooth.async_track_unavailable(
        hass,
        _bparasite_device_unavailable_callback,
        bparasite_device.address,
        connectable=False,
    )

    with patch_bluetooth_time(new_time):
        scanner.inject_advertisement(bparasite_device, bparasite_device_adv, new_time)

    original_device = scanner.discovered_devices_and_advertisement_data[
        bparasite_device.address
    ][0]
    expect(original_device is not bparasite_device).to_be(True)

    for _ in range(1, 20):
        new_time += advertising_interval
        with patch_bluetooth_time(new_time):
            scanner.inject_advertisement(
                bparasite_device, bparasite_device_adv, new_time
            )

    # Make sure the BLEDevice object gets updated
    # and not replaced
    expect(
        scanner.discovered_devices_and_advertisement_data[bparasite_device.address][0]
        is original_device
    ).to_be(True)

    future_time = new_time
    expect(
        bluetooth.async_address_present(hass, bparasite_device.address, False)
    ).to_be(True)
    expect(bparasite_device_went_unavailable).to_be(False)
    with patch_bluetooth_time(new_time):
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=future_time))
        await hass.async_block_till_done()

    expect(bparasite_device_went_unavailable).to_be(False)

    missed_advertisement_future_time = (
        future_time + advertising_interval + TRACKER_BUFFERING_WOBBLE_SECONDS + 1
    )

    with patch_bluetooth_time(missed_advertisement_future_time):
        # Fire once for the scanner to expire the device
        async_fire_time_changed(
            hass, dt_util.utcnow() + timedelta(seconds=UNAVAILABLE_TRACK_SECONDS)
        )
        await hass.async_block_till_done()
        # Fire again for the manager to expire the device
        async_fire_time_changed(
            hass, dt_util.utcnow() + timedelta(seconds=missed_advertisement_future_time)
        )
        await hass.async_block_till_done()

    expect(
        bluetooth.async_address_present(hass, bparasite_device.address, False)
    ).to_be(False)
    expect(bparasite_device_went_unavailable).to_be(True)
    bparasite_device_unavailable_cancel()

    cancel()
    unsetup()


@test
async def scanner_stops_responding(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _enable_bluetooth: None = Depends(enable_bluetooth_fixture),
) -> None:
    """Test we mark a scanner are not scanning when it stops responding."""
    manager = _get_manager()

    connector = (
        HaBluetoothConnector(MockBleakClient, "mock_bleak_client", lambda: False),
    )
    scanner = FakeScanner("esp32", "esp32", connector, True)
    unsetup = scanner.async_setup()
    cancel = manager.async_register_scanner(scanner)

    start_time_monotonic = time.monotonic()

    expect(scanner.scanning).to_be(True)
    failure_reached_time = (
        start_time_monotonic
        + SCANNER_WATCHDOG_TIMEOUT
        + SCANNER_WATCHDOG_INTERVAL.total_seconds()
    )
    # We hit the timer with no detections, so we reset the adapter and restart the scanner
    with patch_bluetooth_time(failure_reached_time):
        async_fire_time_changed(hass, dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL)
        await hass.async_block_till_done()

    expect(scanner.scanning).to_be(False)

    bparasite_device = generate_ble_device(
        "44:44:33:11:23:45",
        "bparasite",
        {},
    )
    bparasite_device_adv = generate_advertisement_data(
        local_name="bparasite",
        service_uuids=[],
        manufacturer_data={1: b"\x01"},
        rssi=-100,
    )

    failure_reached_time += 1

    with patch_bluetooth_time(failure_reached_time):
        scanner.inject_advertisement(
            bparasite_device, bparasite_device_adv, failure_reached_time
        )

    # As soon as we get a detection, we know the scanner is working again
    expect(scanner.scanning).to_be(True)

    cancel()
    unsetup()


@test.cases(
    test.case("test", manufacturer="test", source="test"),
    test.case(
        "raspberry_pi",
        manufacturer="Raspberry Pi Trading Ltd (test)",
        source="28:CD:C1:11:23:45",
    ),
)
async def remote_scanner_bluetooth_config_entry(
    manufacturer: str,
    source: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _enable_bluetooth: None = Depends(enable_bluetooth_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test the remote scanner gets a bluetooth config entry."""
    manager: HomeAssistantBluetoothManager = _get_manager()

    switchbot_device = generate_ble_device(
        "44:44:33:11:23:45",
        "wohand",
        {},
    )
    switchbot_device_adv = generate_advertisement_data(
        local_name="wohand",
        service_uuids=[],
        manufacturer_data={1: b"\x01"},
        rssi=-100,
    )

    connector = (
        HaBluetoothConnector(MockBleakClient, "mock_bleak_client", lambda: False),
    )
    scanner = FakeScanner(source, source, connector, True)
    unsetup = scanner.async_setup()
    expect(scanner.source).to_equal(source)
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)
    cancel = manager.async_register_hass_scanner(
        scanner,
        source_domain="test",
        source_model="test",
        source_config_entry_id=entry.entry_id,
    )
    await hass.async_block_till_done()

    scanner.inject_advertisement(switchbot_device, switchbot_device_adv)
    expect(len(scanner.discovered_devices)).to_equal(1)

    cancel()
    unsetup()

    adapter_entry = hass.config_entries.async_entry_for_domain_unique_id(
        "bluetooth", scanner.source
    )
    expect(adapter_entry is not None).to_be(True)
    expect(adapter_entry.state).to_be(ConfigEntryState.LOADED)

    dev = device_registry.async_get_device(
        connections={(dr.CONNECTION_BLUETOOTH, scanner.source)}
    )
    expect(dev is not None).to_be(True)
    expect(dev.config_entries).to_equal({adapter_entry.entry_id})
    expect(dev.manufacturer).to_equal(manufacturer)

    manager.async_remove_scanner(scanner.source)
    await hass.async_block_till_done()
    expect(
        hass.config_entries.async_entry_for_domain_unique_id(
            "bluetooth", scanner.source
        )
    ).to_be(None)
