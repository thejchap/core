"""Test Xiaomi BLE sensors (tryke port)."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import ATTR_STATE_CLASS
from homeassistant.components.xiaomi_ble.const import DOMAIN
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant

from . import (
    HHCCJCY10_SERVICE_INFO,
    MISCALE_V1_SERVICE_INFO,
    MISCALE_V2_SERVICE_INFO,
    MMC_T201_1_SERVICE_INFO,
    make_advertisement,
)
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
async def sensors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up creates the sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="00:81:F9:DD:6F:C1",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    inject_bluetooth_service_info_bleak(hass, MMC_T201_1_SERVICE_INFO)
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(2)

    # Find the temperature sensor by state value (entity_id slug differs
    # without compiled translations).
    states = hass.states.async_all("sensor")
    temp_states = [s for s in states if s.state == "36.8719980616822"]
    expect(len(temp_states)).to_equal(1)
    expect(temp_states[0].attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("°C")
    expect(temp_states[0].attributes[ATTR_STATE_CLASS]).to_equal("measurement")

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def xiaomi_formaldeyhde(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Make sure that formaldehyde sensors are correctly mapped."""
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
            "C4:7C:8D:6A:3E:7A", b"q \x5d\x01iz>j\x8d|\xc4\r\x10\x10\x02\xf4\x00"
        ),
    )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(1)

    states = hass.states.async_all("sensor")
    expect(len(states)).to_equal(1)
    sensor = states[0]
    expect(sensor.state).to_equal("2.44")
    expect(sensor.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("mg/m³")
    expect(sensor.attributes[ATTR_STATE_CLASS]).to_equal("measurement")

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def xiaomi_consumable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Make sure that consumable sensors are correctly mapped."""
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
            "C4:7C:8D:6A:3E:7A", b"q \x5d\x01iz>j\x8d|\xc4\r\x13\x10\x02\x60\x00"
        ),
    )

    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(1)

    states = hass.states.async_all("sensor")
    expect(len(states)).to_equal(1)
    sensor = states[0]
    expect(sensor.state).to_equal("96")
    expect(sensor.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("%")
    expect(sensor.attributes[ATTR_STATE_CLASS]).to_equal("measurement")

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def xiaomi_score(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Make sure that score sensors are correctly mapped."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="ED:DE:34:3F:48:0C",
        data={"bindkey": "1330b99cded13258acc391627e9771f7"},
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "ED:DE:34:3F:48:0C",
            b"\x48\x58\x06\x08\xc9H\x0e\xf1\x12\x81\x07\x973\xfc\x14\x00\x00VD\xdbA",
        ),
    )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(2)

    states = hass.states.async_all("sensor")
    score_states = [s for s in states if s.state == "83"]
    expect(len(score_states)).to_equal(1)
    expect(score_states[0].attributes[ATTR_STATE_CLASS]).to_equal("measurement")

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def xiaomi_battery_voltage(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Make sure that battery voltage sensors are correctly mapped."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="C4:7C:8D:6A:3E:7A",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "C4:7C:8D:6A:3E:7A", b"q \x5d\x01iz>j\x8d|\xc4\r\x0a\x10\x02\x64\x00"
        ),
    )

    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(2)

    states = hass.states.async_all("sensor")
    volt_states = [s for s in states if s.state == "3.1"]
    expect(len(volt_states)).to_equal(1)
    expect(volt_states[0].attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("V")
    expect(volt_states[0].attributes[ATTR_STATE_CLASS]).to_equal("measurement")

    bat_states = [s for s in states if s.state == "100"]
    expect(len(bat_states)).to_equal(1)
    expect(bat_states[0].attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("%")
    expect(bat_states[0].attributes[ATTR_STATE_CLASS]).to_equal("measurement")

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def xiaomi_hhccjcy01(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HHCCJCY01 multiple advertisements."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="C4:7C:8D:6A:3E:7A",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    for payload in (
        b"q \x98\x00fz>j\x8d|\xc4\r\x07\x10\x03\x00\x00\x00",
        b"q \x98\x00hz>j\x8d|\xc4\r\t\x10\x02W\x02",
        b"q \x98\x00Gz>j\x8d|\xc4\r\x08\x10\x01@",
        b"q \x98\x00iz>j\x8d|\xc4\r\x04\x10\x02\xf4\x00",
    ):
        inject_bluetooth_service_info_bleak(
            hass, make_advertisement("C4:7C:8D:6A:3E:7A", payload)
        )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(5)

    states = hass.states.async_all("sensor")
    state_map = {s.state: s for s in states}
    expect("0" in state_map).to_be(True)
    expect(state_map["0"].attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("lx")
    expect("599" in state_map).to_be(True)
    expect(state_map["599"].attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("μS/cm")
    expect("64" in state_map).to_be(True)
    expect(state_map["64"].attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("%")
    expect("24.4" in state_map).to_be(True)
    expect(state_map["24.4"].attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("°C")
    expect("5" in state_map).to_be(True)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def xiaomi_hhccjcy01_not_connectable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HHCCJCY01 when sensors are not connectable."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="C4:7C:8D:6A:3E:7A",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    for payload in (
        b"q \x98\x00fz>j\x8d|\xc4\r\x07\x10\x03\x00\x00\x00",
        b"q \x98\x00hz>j\x8d|\xc4\r\t\x10\x02W\x02",
        b"q \x98\x00Gz>j\x8d|\xc4\r\x08\x10\x01@",
        b"q \x98\x00iz>j\x8d|\xc4\r\x04\x10\x02\xf4\x00",
    ):
        inject_bluetooth_service_info_bleak(
            hass,
            make_advertisement("C4:7C:8D:6A:3E:7A", payload, connectable=False),
        )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(4)

    states = hass.states.async_all("sensor")
    state_map = {s.state: s for s in states}
    expect("0" in state_map).to_be(True)
    expect("599" in state_map).to_be(True)
    expect("64" in state_map).to_be(True)
    expect("24.4" in state_map).to_be(True)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def xiaomi_hhccjcy01_only_some_sources_connectable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HHCCJCY01 partial sources connectable."""
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
            "C4:7C:8D:6A:3E:7A",
            b"q \x98\x00fz>j\x8d|\xc4\r\x07\x10\x03\x00\x00\x00",
            connectable=True,
        ),
    )
    for payload in (
        b"q \x98\x00hz>j\x8d|\xc4\r\t\x10\x02W\x02",
        b"q \x98\x00Gz>j\x8d|\xc4\r\x08\x10\x01@",
        b"q \x98\x00iz>j\x8d|\xc4\r\x04\x10\x02\xf4\x00",
    ):
        inject_bluetooth_service_info_bleak(
            hass,
            make_advertisement("C4:7C:8D:6A:3E:7A", payload, connectable=False),
        )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(5)

    states = hass.states.async_all("sensor")
    state_map = {s.state: s for s in states}
    expect("0" in state_map).to_be(True)
    expect("599" in state_map).to_be(True)
    expect("64" in state_map).to_be(True)
    expect("24.4" in state_map).to_be(True)
    expect("5" in state_map).to_be(True)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def xiaomi_cgdk2_bind_key(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test CGDK2 bind key."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="58:2D:34:12:20:89",
        data={"bindkey": "a3bfe9853dd85a620debe3620caaa351"},
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            "58:2D:34:12:20:89",
            b"XXo\x06\x07\x89 \x124-X_\x17m\xd5O\x02\x00\x00/\xa4S\xfa",
        ),
    )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(1)

    states = hass.states.async_all("sensor")
    expect(len(states)).to_equal(1)
    expect(states[0].state).to_equal("22.6")
    expect(states[0].attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("°C")
    expect(states[0].attributes[ATTR_STATE_CLASS]).to_equal("measurement")

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def hhccjcy10_uuid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test HHCCJCY10 UUID."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="DC:23:4D:E5:5B:FC",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    inject_bluetooth_service_info_bleak(hass, HHCCJCY10_SERVICE_INFO)

    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(5)

    states = hass.states.async_all("sensor")
    state_map = {s.state: s for s in states}
    expect("11.0" in state_map).to_be(True)
    expect(state_map["11.0"].attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("°C")
    expect("79012" in state_map).to_be(True)
    expect(state_map["79012"].attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("lx")
    expect("91" in state_map).to_be(True)
    expect(state_map["91"].attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("μS/cm")
    expect("14" in state_map).to_be(True)
    expect("40" in state_map).to_be(True)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def miscale_v1_uuid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test MiScale V1 UUID."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="50:FB:19:1B:B5:DC",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    inject_bluetooth_service_info_bleak(hass, MISCALE_V1_SERVICE_INFO)

    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(2)

    states = hass.states.async_all("sensor")
    weight_states = [s for s in states if s.state == "86.55"]
    expect(len(weight_states)).to_equal(2)
    for s in weight_states:
        expect(s.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("kg")
        expect(s.attributes[ATTR_STATE_CLASS]).to_equal("measurement")

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test
async def miscale_v2_uuid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test MiScale V2 UUID."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="50:FB:19:1B:B5:DC",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    inject_bluetooth_service_info_bleak(hass, MISCALE_V2_SERVICE_INFO)

    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_equal(3)

    states = hass.states.async_all("sensor")
    weight_states = [s for s in states if s.state == "85.15"]
    expect(len(weight_states)).to_equal(2)
    impedance_states = [s for s in states if s.state == "428"]
    expect(len(impedance_states)).to_equal(1)
    expect(impedance_states[0].attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("ohm")

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test.skip("xiaomi_ble: xmosb01xs needs translation injection for entity_id slugs")
async def xiaomi_xmosb01xs() -> None:
    """Stub for test_xiaomi_xmosb01xs."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def unavailable() -> None:
    """Stub for test_unavailable."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def sleepy_device() -> None:
    """Stub for test_sleepy_device."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def sleepy_device_restore_state() -> None:
    """Stub for test_sleepy_device_restore_state."""
