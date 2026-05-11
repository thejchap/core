"""Test Xiaomi binary sensors (tryke port)."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.xiaomi_ble.const import DOMAIN
from homeassistant.const import ATTR_FRIENDLY_NAME, STATE_OFF, STATE_ON
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


@test
async def light_motion(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up a light and motion binary sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="58:2D:34:35:93:21",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "58:2D:34:35:93:21",
            b"P \xf6\x07\xda!\x9354-X\x0f\x00\x03\x01\x00\x00",
        ),
    )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(2)

    states = hass.states.async_all("binary_sensor")
    on_states = [s for s in states if s.state == STATE_ON]
    off_states = [s for s in states if s.state == STATE_OFF]
    expect(len(on_states)).to_equal(1)
    expect(len(off_states)).to_equal(1)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def moisture(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up a moisture binary sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="C4:7C:8D:6A:3E:7A",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "C4:7C:8D:6A:3E:7A", b"q \x5d\x01iz>j\x8d|\xc4\r\x14\x10\x02\xf4\x00"
        ),
    )

    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(1)

    states = hass.states.async_all("binary_sensor")
    expect(len(states)).to_equal(1)
    expect(states[0].state).to_equal(STATE_ON)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def opening(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up an opening binary sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="A4:C1:38:66:E5:67",
        data={"bindkey": "0fdcc30fe9289254876b5ef7c11ef1f0"},
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "A4:C1:38:66:E5:67",
            b"XY\x89\x18\x9ag\xe5f8\xc1\xa4\x9d\xd9z\xf3&\x00\x00\xc8\xa6\x0b\xd5",
        ),
    )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(1)

    states = hass.states.async_all("binary_sensor")
    expect(len(states)).to_equal(1)
    expect(states[0].state).to_equal(STATE_ON)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def opening_problem_sensors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up an opening binary sensor with additional problem sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="A4:C1:38:66:E5:67",
        data={"bindkey": "0fdcc30fe9289254876b5ef7c11ef1f0"},
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "A4:C1:38:66:E5:67",
            b"XY\x89\x18ug\xe5f8\xc1\xa4i\xdd\xf3\xa1&\x00\x00\xa2J\x1bE",
        ),
    )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(3)

    states = hass.states.async_all("binary_sensor")
    expect(len(states)).to_equal(3)
    for s in states:
        expect(s.state).to_equal(STATE_OFF)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def smoke(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up a smoke binary sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="54:EF:44:E3:9C:BC",
        data={"bindkey": "5b51a7c91cde6707c9ef18dfda143a58"},
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "54:EF:44:E3:9C:BC",
            b"XY\x97\tf\xbc\x9c\xe3D\xefT\x01\x08\x12\x05\x00\x00\x00q^\xbe\x90",
        ),
    )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(1)

    states = hass.states.async_all("binary_sensor")
    expect(len(states)).to_equal(1)
    expect(states[0].state).to_equal(STATE_ON)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def power(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up a power binary sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="F8:24:41:E9:50:74",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "F8:24:41:E9:50:74",
            b"P0S\x01?tP\xe9A$\xf8\x01\x10\x03\x01\x00\x00",
        ),
    )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(2)

    states = hass.states.async_all("binary_sensor")
    # power binary_sensor + a sibling sensor
    power_states = [s for s in states if s.state == STATE_OFF]
    expect(len(power_states) >= 1).to_be(True)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def unavailable() -> None:
    """Stub for test_unavailable."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def sleepy_device() -> None:
    """Stub for test_sleepy_device."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def sleepy_device_restore_state() -> None:
    """Stub for test_sleepy_device_restore_state."""
