"""Test Xiaomi binary sensors (tryke port)."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.xiaomi_ble.const import DOMAIN
from homeassistant.const import ATTR_FRIENDLY_NAME, STATE_OFF
from homeassistant.core import HomeAssistant

from . import make_advertisement
from .conftest import MockBleakClientBattery5

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info_bleak
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


@fixture
def mock_bluetooth_xiaomi() -> Generator[None]:
    """Auto mock the BleakClient (replaces xiaomi_ble conftest autouse)."""
    with patch("xiaomi_ble.parser.BleakClient", MockBleakClientBattery5):
        yield


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
    _mock_bleak: None = Depends(mock_bluetooth_xiaomi),
) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test
async def door_problem_sensors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up a door binary sensor with additional problem sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="EE:89:73:44:BE:98",
        data={"bindkey": "2c3795afa33019a8afdc17ba99e6f217"},
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_be(0)
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "EE:89:73:44:BE:98",
            b"HU9\x0e3\x9cq\xc0$\x1f\xff\xee\x80S\x00\x00\x02\xb4\xc59",
        ),
    )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_be(3)

    door_sensor = hass.states.get("binary_sensor.door_lock_be98_door")
    expect(door_sensor is not None).to_be(True)
    expect(door_sensor.state).to_equal(STATE_OFF)
    expect(door_sensor.attributes[ATTR_FRIENDLY_NAME]).to_equal(
        "Door Lock BE98 Door"
    )

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def light_motion() -> None:
    """Stub for test_light_motion."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def moisture() -> None:
    """Stub for test_moisture."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def opening() -> None:
    """Stub for test_opening."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def opening_problem_sensors() -> None:
    """Stub for test_opening_problem_sensors."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def smoke() -> None:
    """Stub for test_smoke."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def power() -> None:
    """Stub for test_power."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def unavailable() -> None:
    """Stub for test_unavailable."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def sleepy_device() -> None:
    """Stub for test_sleepy_device."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def sleepy_device_restore_state() -> None:
    """Stub for test_sleepy_device_restore_state."""
