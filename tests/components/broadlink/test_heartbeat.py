"""Tests for Broadlink heartbeats."""

from collections.abc import Generator
from unittest.mock import call, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.broadlink.heartbeat import BroadlinkHeartbeat
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from . import get_device

from tests.common import async_fire_time_changed
from tests.hass_fixtures import LogCapture
from tests.hass_fixtures import caplog as caplog_fixture
from tests.hass_fixtures import hass as hass_fixture

DEVICE_PING = "homeassistant.components.broadlink.heartbeat.blk.ping"


@fixture
def _autouse_heartbeat() -> Generator[None]:
    """Mock broadlink heartbeat (mirrors conftest autouse)."""
    with patch(DEVICE_PING):
        yield


@fixture
def _trigger_executor(
    _autouse: None = Depends(_autouse_heartbeat),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def heartbeat_trigger_startup(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that the heartbeat is initialized with the first config entry."""
    device = get_device("Office")

    with patch(DEVICE_PING) as mock_ping:
        await device.setup_entry(hass)
        await hass.async_block_till_done()

    expect(mock_ping.call_count).to_equal(1)
    expect(mock_ping.call_args).to_equal(call(device.host))


@test
async def heartbeat_ignore_oserror(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that an OSError is ignored."""
    device = get_device("Office")

    with patch(DEVICE_PING, side_effect=OSError()):
        await device.setup_entry(hass)
        await hass.async_block_till_done()

    expect("Failed to send heartbeat to" in caplog.text).to_be(True)


@test
async def heartbeat_trigger_right_time(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that the heartbeat is triggered at the right time."""
    device = get_device("Office")

    await device.setup_entry(hass)
    await hass.async_block_till_done()

    with patch(DEVICE_PING) as mock_ping:
        async_fire_time_changed(
            hass, dt_util.utcnow() + BroadlinkHeartbeat.HEARTBEAT_INTERVAL
        )
        await hass.async_block_till_done(wait_background_tasks=True)

    expect(mock_ping.call_count).to_equal(1)
    expect(mock_ping.call_args).to_equal(call(device.host))


@test
async def heartbeat_do_not_trigger_before_time(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that the heartbeat is not triggered before the time."""
    device = get_device("Office")

    await device.setup_entry(hass)
    await hass.async_block_till_done()

    with patch(DEVICE_PING) as mock_ping:
        async_fire_time_changed(
            hass,
            dt_util.utcnow() + BroadlinkHeartbeat.HEARTBEAT_INTERVAL // 2,
        )
        await hass.async_block_till_done(wait_background_tasks=True)

    expect(mock_ping.call_count).to_equal(0)


@test
async def heartbeat_unload(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that the heartbeat is deactivated when the last config entry is removed."""
    device = get_device("Office")

    mock_setup = await device.setup_entry(hass)
    await hass.async_block_till_done()

    await hass.config_entries.async_remove(mock_setup.entry.entry_id)
    await hass.async_block_till_done()

    with patch(DEVICE_PING) as mock_ping:
        async_fire_time_changed(
            hass, dt_util.utcnow() + BroadlinkHeartbeat.HEARTBEAT_INTERVAL
        )
        await hass.async_block_till_done(wait_background_tasks=True)

    expect(mock_ping.call_count).to_equal(0)


@test
async def heartbeat_do_not_unload(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that the heartbeat is not deactivated until the last config entry is removed."""
    device_a = get_device("Office")
    device_b = get_device("Bedroom")

    mock_setup = await device_a.setup_entry(hass)
    await device_b.setup_entry(hass)
    await hass.async_block_till_done()

    await hass.config_entries.async_remove(mock_setup.entry.entry_id)
    await hass.async_block_till_done()

    with patch(DEVICE_PING) as mock_ping:
        async_fire_time_changed(
            hass, dt_util.utcnow() + BroadlinkHeartbeat.HEARTBEAT_INTERVAL
        )
        await hass.async_block_till_done(wait_background_tasks=True)

    expect(mock_ping.call_count).to_equal(1)
    expect(mock_ping.call_args).to_equal(call(device_b.host))
