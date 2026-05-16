"""The tests for the Rfxtrx sensor platform."""

from collections.abc import Callable, Coroutine
from typing import Any
from unittest.mock import Mock

from tryke import Depends, expect, fixture, test

from homeassistant.components.rfxtrx import DOMAIN
from homeassistant.components.rfxtrx.const import ATTR_EVENT
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State

from ._fixtures import (
    create_rfx_test_cfg,
    rfxtrx_automatic_fx,
    rfxtrx_fx,
    timestep_fx,
)

from tests.common import MockConfigEntry, mock_restore_cache
from tests.hass_fixtures import hass as hass_fixture

EVENT_SMOKE_DETECTOR_PANIC = "08200300a109000670"
EVENT_SMOKE_DETECTOR_NO_PANIC = "08200300a109000770"

EVENT_MOTION_DETECTOR_MOTION = "08200100a109000470"
EVENT_MOTION_DETECTOR_NO_MOTION = "08200100a109000570"

EVENT_LIGHT_DETECTOR_LIGHT = "08200100a109001570"
EVENT_LIGHT_DETECTOR_DARK = "08200100a109001470"

EVENT_AC_118CDEA_2_ON = "0b1100100118cdea02010f70"


@fixture
def _trigger_executor() -> int:
    return 0


@test
async def one(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
) -> None:
    """Test with 1 sensor."""
    entry_data = create_rfx_test_cfg(devices={"0b1100cd0213c7f230010f71": {}})
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.ac_213c7f2_48")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get("friendly_name")).to_equal("AC 213c7f2:48")


@test
async def one_pt2262(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
) -> None:
    """Test with 1 PT2262 sensor."""
    entry_data = create_rfx_test_cfg(
        devices={
            "0913000022670e013970": {
                "data_bits": 4,
                "command_on": 0xE,
                "command_off": 0x7,
            }
        }
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    await hass.async_start()

    state = hass.states.get("binary_sensor.pt2262_226700")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get("friendly_name")).to_equal("PT2262 226700")

    await rfxtrx.signal("0913000022670e013970")
    state = hass.states.get("binary_sensor.pt2262_226700")
    expect(state.state).to_equal("on")

    await rfxtrx.signal("09130000226707013d70")
    state = hass.states.get("binary_sensor.pt2262_226700")
    expect(state.state).to_equal("off")


@test
async def pt2262_unconfigured(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
) -> None:
    """Test with discovery for PT2262."""
    entry_data = create_rfx_test_cfg(
        devices={"0913000022670e013970": {}, "09130000226707013970": {}}
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    await hass.async_start()

    state = hass.states.get("binary_sensor.pt2262_226707")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get("friendly_name")).to_equal("PT2262 226707")

    state = hass.states.get("binary_sensor.pt2262_226707")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get("friendly_name")).to_equal("PT2262 226707")


@test.cases(
    test.case("on", state="on", event="0b1100cd0213c7f230010f71"),
    test.case("off", state="off", event="0b1100cd0213c7f230000f71"),
)
async def state_restore(
    state: str,
    event: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
) -> None:
    """State restoration."""

    entity_id = "binary_sensor.ac_213c7f2_48"

    mock_restore_cache(hass, [State(entity_id, state, attributes={ATTR_EVENT: event})])

    entry_data = create_rfx_test_cfg(devices={"0b1100cd0213c7f230010f71": {}})
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    expect(hass.states.get(entity_id).state).to_equal(state)


@test
async def several(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
) -> None:
    """Test with 3."""
    entry_data = create_rfx_test_cfg(
        devices={
            "0b1100cd0213c7f230010f71": {},
            "0b1100100118cdea02010f70": {},
            "0b1100100118cdea03010f70": {},
        }
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.ac_213c7f2_48")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get("friendly_name")).to_equal("AC 213c7f2:48")

    state = hass.states.get("binary_sensor.ac_118cdea_2")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get("friendly_name")).to_equal("AC 118cdea:2")

    state = hass.states.get("binary_sensor.ac_118cdea_3")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get("friendly_name")).to_equal("AC 118cdea:3")

    # "2: Group on"
    await rfxtrx.signal("0b1100100118cdea03040f70")
    expect(hass.states.get("binary_sensor.ac_118cdea_2").state).to_equal("on")
    expect(hass.states.get("binary_sensor.ac_118cdea_3").state).to_equal("on")

    # "2: Group off"
    await rfxtrx.signal("0b1100100118cdea03030f70")
    expect(hass.states.get("binary_sensor.ac_118cdea_2").state).to_equal("off")
    expect(hass.states.get("binary_sensor.ac_118cdea_3").state).to_equal("off")


@test
async def discover(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx_automatic: Mock = Depends(rfxtrx_automatic_fx),
) -> None:
    """Test with discovery."""
    rfxtrx = rfxtrx_automatic

    await rfxtrx.signal("0b1100100118cdea02010f70")
    state = hass.states.get("binary_sensor.ac_118cdea_2")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("on")

    await rfxtrx.signal("0b1100100118cdeb02010f70")
    state = hass.states.get("binary_sensor.ac_118cdeb_2")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("on")


@test
async def off_delay_restore(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
) -> None:
    """Make sure binary sensor restore as off, if off delay is active."""
    mock_restore_cache(
        hass,
        [
            State(
                "binary_sensor.ac_118cdea_2",
                "on",
                attributes={ATTR_EVENT: EVENT_AC_118CDEA_2_ON},
            )
        ],
    )

    entry_data = create_rfx_test_cfg(devices={EVENT_AC_118CDEA_2_ON: {"off_delay": 5}})
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    await hass.async_start()

    state = hass.states.get("binary_sensor.ac_118cdea_2")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("off")


@test
async def off_delay(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
    timestep: Callable[[int], Coroutine[Any, Any, None]] = Depends(timestep_fx),
) -> None:
    """Test with discovery."""
    entry_data = create_rfx_test_cfg(
        devices={"0b1100100118cdea02010f70": {"off_delay": 5}}
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    await hass.async_start()

    state = hass.states.get("binary_sensor.ac_118cdea_2")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)

    await rfxtrx.signal("0b1100100118cdea02010f70")
    state = hass.states.get("binary_sensor.ac_118cdea_2")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("on")

    await timestep(4)
    state = hass.states.get("binary_sensor.ac_118cdea_2")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("on")

    await timestep(4)
    state = hass.states.get("binary_sensor.ac_118cdea_2")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("off")

    await rfxtrx.signal("0b1100100118cdea02010f70")
    state = hass.states.get("binary_sensor.ac_118cdea_2")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("on")

    await timestep(3)
    await rfxtrx.signal("0b1100100118cdea02010f70")

    await timestep(4)
    state = hass.states.get("binary_sensor.ac_118cdea_2")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("on")

    await timestep(4)
    state = hass.states.get("binary_sensor.ac_118cdea_2")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("off")


@test
async def panic(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx_automatic: Mock = Depends(rfxtrx_automatic_fx),
) -> None:
    """Test panic entities."""
    rfxtrx = rfxtrx_automatic

    entity_id = "binary_sensor.kd101_smoke_detector_a10900_32"

    await rfxtrx.signal(EVENT_SMOKE_DETECTOR_PANIC)
    expect(hass.states.get(entity_id).state).to_equal("on")
    expect(hass.states.get(entity_id).attributes.get("device_class")).to_equal("smoke")

    await rfxtrx.signal(EVENT_SMOKE_DETECTOR_NO_PANIC)
    expect(hass.states.get(entity_id).state).to_equal("off")


@test
async def motion(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx_automatic: Mock = Depends(rfxtrx_automatic_fx),
) -> None:
    """Test motion entities."""
    rfxtrx = rfxtrx_automatic

    entity_id = "binary_sensor.x10_security_motion_detector_a10900_32"

    await rfxtrx.signal(EVENT_MOTION_DETECTOR_MOTION)
    expect(hass.states.get(entity_id).state).to_equal("on")
    expect(hass.states.get(entity_id).attributes.get("device_class")).to_equal("motion")

    await rfxtrx.signal(EVENT_MOTION_DETECTOR_NO_MOTION)
    expect(hass.states.get(entity_id).state).to_equal("off")


@test
async def light(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx_automatic: Mock = Depends(rfxtrx_automatic_fx),
) -> None:
    """Test light entities."""
    rfxtrx = rfxtrx_automatic

    entity_id = "binary_sensor.x10_security_motion_detector_a10900_32"

    await rfxtrx.signal(EVENT_LIGHT_DETECTOR_LIGHT)
    expect(hass.states.get(entity_id).state).to_equal("on")

    await rfxtrx.signal(EVENT_LIGHT_DETECTOR_DARK)
    expect(hass.states.get(entity_id).state).to_equal("off")


@test
async def pt2262_duplicate_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rfxtrx: Mock = Depends(rfxtrx_fx),
) -> None:
    """Test with 1 sensor."""
    entry_data = create_rfx_test_cfg(
        devices={
            "0913000022670e013970": {
                "data_bits": 4,
                "command_on": 0xE,
                "command_off": 0x7,
            },
            "09130000226707013970": {
                "data_bits": 4,
                "command_on": 0xE,
                "command_off": 0x7,
            },
        }
    )
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    await hass.async_start()

    state = hass.states.get("binary_sensor.pt2262_226700")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get("friendly_name")).to_equal("PT2262 226700")
