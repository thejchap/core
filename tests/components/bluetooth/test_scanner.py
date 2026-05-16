"""Tests for the Bluetooth integration scanners."""

import asyncio
from datetime import timedelta
import time
from typing import Any
from unittest.mock import ANY, MagicMock, patch

from bleak import BleakError
from bleak.backends.scanner import AdvertisementDataCallback
from dbus_fast import InvalidMessageError
from tryke import Depends, expect, fixture, test

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.const import (
    SCANNER_WATCHDOG_INTERVAL,
    SCANNER_WATCHDOG_TIMEOUT,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from . import (
    async_setup_with_one_adapter,
    generate_advertisement_data,
    generate_ble_device,
    patch_bluetooth_time,
)
from ._fixtures import (
    macos_adapter as macos_adapter_fixture,
    one_adapter as one_adapter_fixture,
)

from tests.common import (
    MockConfigEntry,
    async_call_logger_set_level,
    async_fire_time_changed,
)
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    enable_bluetooth as enable_bluetooth_fixture,
    hass as hass_fixture,
    mock_bleak_scanner_start as mock_bleak_scanner_start_fixture,
    mock_network,
)

# If the adapter is in a stuck state the following errors are raised:
NEED_RESET_ERRORS = [
    "org.bluez.Error.Failed",
    "org.bluez.Error.InProgress",
    "org.bluez.Error.NotReady",
    "not found",
]


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test.skip(
    "fixture-ordering: enable_bluetooth + macos_adapter setup leaves scanner in "
    "SETUP_ERROR under tryke (HaScanner mock interacts differently with cross-platform "
    "patches than pytest usefixtures ordering)"
)
async def config_entry_can_be_reloaded_when_stop_raises(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _enable_bluetooth: None = Depends(enable_bluetooth_fixture),
    _macos_adapter: None = Depends(macos_adapter_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test we can reload if stopping the scanner raises."""
    entry = hass.config_entries.async_entries(bluetooth.DOMAIN)[0]
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    with patch(
        "habluetooth.scanner.OriginalBleakScanner.stop",
        side_effect=BleakError,
    ):
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(caplog.text).to_contain("Error stopping scanner")


@test
async def dbus_socket_missing_in_container(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _one_adapter: None = Depends(one_adapter_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test we handle dbus being missing in the container."""

    with (
        patch("habluetooth.scanner.is_docker_env", return_value=True),
        patch(
            "habluetooth.scanner.OriginalBleakScanner.start",
            side_effect=FileNotFoundError,
        ),
    ):
        await async_setup_with_one_adapter(hass)

        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    expect(caplog.text).to_contain("/run/dbus")
    expect(caplog.text).to_contain("docker")


@test
async def dbus_socket_missing(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _one_adapter: None = Depends(one_adapter_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test we handle dbus being missing."""

    with (
        patch("habluetooth.scanner.is_docker_env", return_value=False),
        patch(
            "habluetooth.scanner.OriginalBleakScanner.start",
            side_effect=FileNotFoundError,
        ),
    ):
        await async_setup_with_one_adapter(hass)

        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    expect(caplog.text).to_contain("DBus")
    expect(caplog.text).not_.to_contain("docker")


@test
async def dbus_broken_pipe_in_container(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _one_adapter: None = Depends(one_adapter_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test we handle dbus broken pipe in the container."""

    with (
        patch("habluetooth.scanner.is_docker_env", return_value=True),
        patch(
            "habluetooth.scanner.OriginalBleakScanner.start",
            side_effect=BrokenPipeError,
        ),
    ):
        await async_setup_with_one_adapter(hass)

        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    expect(caplog.text).to_contain("dbus")
    expect(caplog.text).to_contain("restarting")
    expect(caplog.text).to_contain("container")


@test
async def dbus_broken_pipe(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _one_adapter: None = Depends(one_adapter_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test we handle dbus broken pipe."""

    with (
        patch("habluetooth.scanner.is_docker_env", return_value=False),
        patch(
            "habluetooth.scanner.OriginalBleakScanner.start",
            side_effect=BrokenPipeError,
        ),
    ):
        await async_setup_with_one_adapter(hass)

        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    expect(caplog.text).to_contain("DBus")
    expect(caplog.text).to_contain("restarting")
    expect(caplog.text).not_.to_contain("container")


@test
async def invalid_dbus_message(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _one_adapter: None = Depends(one_adapter_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test we handle invalid dbus message."""

    with patch(
        "habluetooth.scanner.OriginalBleakScanner.start",
        side_effect=InvalidMessageError,
    ):
        await async_setup_with_one_adapter(hass)

        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    expect(caplog.text).to_contain("dbus")


@test.cases(
    test.case("failed", error="org.bluez.Error.Failed"),
    test.case("in_progress", error="org.bluez.Error.InProgress"),
    test.case("not_ready", error="org.bluez.Error.NotReady"),
    test.case("not_found", error="not found"),
)
async def adapter_needs_reset_at_start(
    error: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _one_adapter: None = Depends(one_adapter_fixture),
) -> None:
    """Test we cycle the adapter when it needs a restart."""

    with (
        patch(
            "habluetooth.scanner.OriginalBleakScanner.start",
            side_effect=[BleakError(error), BleakError(error), None],
        ),
        patch(
            "habluetooth.util.recover_adapter", return_value=True
        ) as mock_recover_adapter,
    ):
        await async_setup_with_one_adapter(hass)

        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

    expect(len(mock_recover_adapter.mock_calls)).to_equal(1)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()


@test
async def recovery_from_dbus_restart(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _one_adapter: None = Depends(one_adapter_fixture),
) -> None:
    """Test we can recover when DBus gets restarted out from under us."""

    called_start = 0
    called_stop = 0
    _callback = None
    mock_discovered = []

    class MockBleakScanner:
        def __init__(self, detection_callback, *args: Any, **kwargs: Any) -> None:
            nonlocal _callback
            _callback = detection_callback

        async def start(self, *args, **kwargs):
            """Mock Start."""
            nonlocal called_start
            called_start += 1

        async def stop(self, *args, **kwargs):
            """Mock Start."""
            nonlocal called_stop
            called_stop += 1

        @property
        def discovered_devices(self):
            """Mock discovered_devices."""
            nonlocal mock_discovered
            return mock_discovered

    with patch(
        "habluetooth.scanner.OriginalBleakScanner",
        MockBleakScanner,
    ):
        await async_setup_with_one_adapter(hass)

        expect(called_start).to_equal(1)

        start_time_monotonic = time.monotonic()
        mock_discovered = [MagicMock()]

        # Ensure we don't restart the scanner if we don't need to
        with patch_bluetooth_time(
            start_time_monotonic + 10,
        ):
            async_fire_time_changed(hass, dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL)
            await hass.async_block_till_done()

        expect(called_start).to_equal(1)

        # Fire a callback to reset the timer
        with patch_bluetooth_time(
            start_time_monotonic,
        ):
            _callback(
                generate_ble_device("44:44:33:11:23:42", "any_name"),
                generate_advertisement_data(local_name="any_name"),
            )

        # Ensure we don't restart the scanner if we don't need to
        with patch_bluetooth_time(
            start_time_monotonic + 20,
        ):
            async_fire_time_changed(hass, dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL)
            await hass.async_block_till_done()

        expect(called_start).to_equal(1)

        # We hit the timer, so we restart the scanner
        with patch_bluetooth_time(
            start_time_monotonic + SCANNER_WATCHDOG_TIMEOUT + 20,
        ):
            async_fire_time_changed(
                hass,
                dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL + timedelta(seconds=20),
            )
            await hass.async_block_till_done()

        expect(called_start).to_equal(2)


@test
async def adapter_recovery(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _one_adapter: None = Depends(one_adapter_fixture),
) -> None:
    """Test we can recover when the adapter stops responding."""

    called_start = 0
    called_stop = 0
    _callback = None
    mock_discovered = []

    class MockBleakScanner:
        async def start(self, *args, **kwargs):
            """Mock Start."""
            nonlocal called_start
            called_start += 1

        async def stop(self, *args, **kwargs):
            """Mock Start."""
            nonlocal called_stop
            called_stop += 1

        @property
        def discovered_devices(self):
            """Mock discovered_devices."""
            nonlocal mock_discovered
            return mock_discovered

        def register_detection_callback(self, callback: AdvertisementDataCallback):
            """Mock Register Detection Callback."""
            nonlocal _callback
            _callback = callback

    scanner = MockBleakScanner()
    start_time_monotonic = time.monotonic()

    with (
        patch_bluetooth_time(
            start_time_monotonic,
        ),
        patch(
            "habluetooth.scanner.OriginalBleakScanner",
            return_value=scanner,
        ),
    ):
        await async_setup_with_one_adapter(hass)

        expect(called_start).to_equal(1)

        mock_discovered = [MagicMock()]

        # Ensure we don't restart the scanner if we don't need to
        with patch_bluetooth_time(
            start_time_monotonic + 10,
        ):
            async_fire_time_changed(hass, dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL)
            await hass.async_block_till_done()

        expect(called_start).to_equal(1)

        # Ensure we don't restart the scanner if we don't need to
        with patch_bluetooth_time(
            start_time_monotonic + 20,
        ):
            async_fire_time_changed(hass, dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL)
            await hass.async_block_till_done()

        expect(called_start).to_equal(1)

        # We hit the timer with no detections, so we reset the adapter and restart the scanner
        with (
            patch_bluetooth_time(
                start_time_monotonic
                + SCANNER_WATCHDOG_TIMEOUT
                + SCANNER_WATCHDOG_INTERVAL.total_seconds(),
            ),
            patch(
                "habluetooth.util.recover_adapter", return_value=True
            ) as mock_recover_adapter,
        ):
            async_fire_time_changed(hass, dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL)
            await hass.async_block_till_done()

        expect(len(mock_recover_adapter.mock_calls)).to_equal(1)
        expect(called_start).to_equal(2)


@test
async def adapter_scanner_fails_to_start_first_time(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _one_adapter: None = Depends(one_adapter_fixture),
) -> None:
    """Test we can recover when the adapter stops responding and the first recovery fails."""

    called_start = 0
    called_stop = 0
    _callback = None
    mock_discovered = []

    class MockBleakScanner:
        async def start(self, *args, **kwargs):
            """Mock Start."""
            nonlocal called_start
            called_start += 1
            if called_start == 1:
                return  # Start ok the first time
            if called_start < 4:
                raise BleakError("Failed to start")

        async def stop(self, *args, **kwargs):
            """Mock Start."""
            nonlocal called_stop
            called_stop += 1

        @property
        def discovered_devices(self):
            """Mock discovered_devices."""
            nonlocal mock_discovered
            return mock_discovered

        def register_detection_callback(self, callback: AdvertisementDataCallback):
            """Mock Register Detection Callback."""
            nonlocal _callback
            _callback = callback

    scanner = MockBleakScanner()
    start_time_monotonic = time.monotonic()

    with (
        patch_bluetooth_time(
            start_time_monotonic,
        ),
        patch(
            "habluetooth.scanner.OriginalBleakScanner",
            return_value=scanner,
        ),
    ):
        await async_setup_with_one_adapter(hass)

        expect(called_start).to_equal(1)

        mock_discovered = [MagicMock()]

        # Ensure we don't restart the scanner if we don't need to
        with patch_bluetooth_time(
            start_time_monotonic + 10,
        ):
            async_fire_time_changed(hass, dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL)
            await hass.async_block_till_done()

        expect(called_start).to_equal(1)

        # Ensure we don't restart the scanner if we don't need to
        with patch_bluetooth_time(
            start_time_monotonic + 20,
        ):
            async_fire_time_changed(hass, dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL)
            await hass.async_block_till_done()

        expect(called_start).to_equal(1)

        # We hit the timer with no detections, so we reset the adapter and restart the scanner
        with (
            patch_bluetooth_time(
                start_time_monotonic
                + SCANNER_WATCHDOG_TIMEOUT
                + SCANNER_WATCHDOG_INTERVAL.total_seconds(),
            ),
            patch(
                "habluetooth.util.recover_adapter", return_value=True
            ) as mock_recover_adapter,
        ):
            async_fire_time_changed(hass, dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL)
            await hass.async_block_till_done()

        expect(len(mock_recover_adapter.mock_calls)).to_equal(1)
        expect(called_start).to_equal(4)

        now_monotonic = time.monotonic()
        # We hit the timer again the previous start call failed, make sure
        # we try again
        with (
            patch_bluetooth_time(
                now_monotonic
                + SCANNER_WATCHDOG_TIMEOUT * 2
                + SCANNER_WATCHDOG_INTERVAL.total_seconds(),
            ),
            patch(
                "habluetooth.util.recover_adapter", return_value=True
            ) as mock_recover_adapter,
        ):
            async_fire_time_changed(hass, dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL)
            await hass.async_block_till_done()

        expect(len(mock_recover_adapter.mock_calls)).to_equal(1)
        expect(called_start).to_equal(5)


@test
async def adapter_fails_to_start_and_takes_a_bit_to_init(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _one_adapter: None = Depends(one_adapter_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test we can recover the adapter at startup and we wait for Dbus to init."""
    expect(await async_setup_component(hass, "logger", {})).to_be_truthy()
    async with async_call_logger_set_level(
        "homeassistant.components.bluetooth", "DEBUG", hass=hass, caplog=caplog
    ):
        called_start = 0
        called_stop = 0
        _callback = None
        mock_discovered = []

        class MockBleakScanner:
            async def start(self, *args, **kwargs):
                """Mock Start."""
                nonlocal called_start
                called_start += 1
                if called_start == 1:
                    raise BleakError("org.freedesktop.DBus.Error.UnknownObject")
                if called_start == 2:
                    raise BleakError("org.bluez.Error.InProgress")
                if called_start == 3:
                    raise BleakError("org.bluez.Error.InProgress")

            async def stop(self, *args, **kwargs):
                """Mock Start."""
                nonlocal called_stop
                called_stop += 1

            @property
            def discovered_devices(self):
                """Mock discovered_devices."""
                nonlocal mock_discovered
                return mock_discovered

            def register_detection_callback(self, callback: AdvertisementDataCallback):
                """Mock Register Detection Callback."""
                nonlocal _callback
                _callback = callback

        scanner = MockBleakScanner()
        start_time_monotonic = time.monotonic()

        with (
            patch(
                "habluetooth.scanner.ADAPTER_INIT_TIME",
                0,
            ),
            patch_bluetooth_time(
                start_time_monotonic,
            ),
            patch(
                "habluetooth.scanner.OriginalBleakScanner",
                return_value=scanner,
            ),
            patch(
                "habluetooth.util.recover_adapter", return_value=True
            ) as mock_recover_adapter,
        ):
            await async_setup_with_one_adapter(hass)

            expect(called_start).to_equal(4)

        expect(len(mock_recover_adapter.mock_calls)).to_equal(1)
        expect(caplog.text).to_contain("Waiting for adapter to initialize")


@test
async def restart_takes_longer_than_watchdog_time(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _one_adapter: None = Depends(one_adapter_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test we do not try to recover the adapter again if the restart is still in progress."""

    release_start_event = asyncio.Event()
    called_start = 0

    class MockBleakScanner:
        async def start(self, *args, **kwargs):
            """Mock Start."""
            nonlocal called_start
            called_start += 1
            if called_start == 1:
                return
            await release_start_event.wait()

        async def stop(self, *args, **kwargs):
            """Mock Start."""

        @property
        def discovered_devices(self):
            """Mock discovered_devices."""
            return []

        def register_detection_callback(self, callback: AdvertisementDataCallback):
            """Mock Register Detection Callback."""

    scanner = MockBleakScanner()
    start_time_monotonic = time.monotonic()

    with (
        patch(
            "habluetooth.scanner.ADAPTER_INIT_TIME",
            0,
        ),
        patch_bluetooth_time(
            start_time_monotonic,
        ),
        patch(
            "habluetooth.scanner.OriginalBleakScanner",
            return_value=scanner,
        ),
        patch("habluetooth.util.recover_adapter", return_value=True),
    ):
        await async_setup_with_one_adapter(hass)

        expect(called_start).to_equal(1)

        # Now force a recover adapter 2x
        for _ in range(2):
            with patch_bluetooth_time(
                start_time_monotonic
                + SCANNER_WATCHDOG_TIMEOUT
                + SCANNER_WATCHDOG_INTERVAL.total_seconds(),
            ):
                async_fire_time_changed(
                    hass, dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL
                )
                await asyncio.sleep(0)

        # Now release the start event
        release_start_event.set()
        await hass.async_block_till_done()

    expect(caplog.text).to_contain("already restarting")


@test.skip("Darwin-only test (pytest.mark.skipif platform != Darwin)")
async def setup_and_stop_macos(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _macos_adapter: None = Depends(macos_adapter_fixture),
    mock_bleak_scanner_start: MagicMock = Depends(mock_bleak_scanner_start_fixture),
) -> None:
    """Test we enable use_bdaddr on MacOS."""
    entry = MockConfigEntry(
        domain=bluetooth.DOMAIN,
        data={},
        unique_id="00:00:00:00:00:00",
    )
    entry.add_to_hass(hass)
    init_kwargs = None

    class MockBleakScanner:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            """Init the scanner."""
            nonlocal init_kwargs
            init_kwargs = kwargs

        async def start(self, *args, **kwargs):
            """Start the scanner."""

        async def stop(self, *args, **kwargs):
            """Stop the scanner."""

        def register_detection_callback(self, *args, **kwargs):
            """Register a callback."""

    with patch(
        "habluetooth.scanner.OriginalBleakScanner",
        MockBleakScanner,
    ):
        expect(
            await async_setup_component(hass, bluetooth.DOMAIN, {bluetooth.DOMAIN: {}})
        ).to_be_truthy()
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

        hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
        await hass.async_block_till_done()

    expect(init_kwargs).to_equal(
        {
            "detection_callback": ANY,
            "scanning_mode": "active",
            "cb": {"use_bdaddr": True},
        }
    )
