"""Test different accessory types: Locks (tryke port)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components import lock
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.event import EventDeviceClass
from homeassistant.components.homekit.accessories import HomeBridge, HomeDriver
from homeassistant.components.homekit.const import (
    ATTR_VALUE,
    CHAR_PROGRAMMABLE_SWITCH_EVENT,
    CONF_LINKED_DOORBELL_SENSOR,
    SERV_DOORBELL,
    SERV_STATELESS_PROGRAMMABLE_SWITCH,
)
from homeassistant.components.homekit.type_locks import Lock
from homeassistant.components.lock import DOMAIN as LOCK_DOMAIN, LockState
from homeassistant.const import (
    ATTR_CODE,
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_mock_service
from tests.components.homekit._fixtures import (
    events as events_fixture,
    hk_driver as hk_driver_fixture,
)
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (see PATTERNS.md)."""
    return hass


@test
async def lock_unlock(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
    events: list[Event] = Depends(events_fixture),
) -> None:
    """Test if accessory and HA are updated accordingly."""
    code = "1234"
    config = {ATTR_CODE: code}
    entity_id = "lock.kitchen_door"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = Lock(hass, hk_driver, "Lock", entity_id, 2, config)
    acc.run()

    expect(acc.aid).to_be(2)
    expect(acc.category).to_be(6)  # DoorLock

    expect(acc.char_current_state.value).to_be(3)
    expect(acc.char_target_state.value).to_be(1)

    hass.states.async_set(entity_id, LockState.LOCKED)
    await hass.async_block_till_done()
    expect(acc.char_current_state.value).to_be(1)
    expect(acc.char_target_state.value).to_be(1)

    hass.states.async_set(entity_id, LockState.LOCKING)
    await hass.async_block_till_done()
    expect(acc.char_current_state.value).to_be(0)
    expect(acc.char_target_state.value).to_be(1)

    hass.states.async_set(entity_id, LockState.UNLOCKED)
    await hass.async_block_till_done()
    expect(acc.char_current_state.value).to_be(0)
    expect(acc.char_target_state.value).to_be(0)

    hass.states.async_set(entity_id, LockState.UNLOCKING)
    await hass.async_block_till_done()
    expect(acc.char_current_state.value).to_be(1)
    expect(acc.char_target_state.value).to_be(0)

    hass.states.async_set(entity_id, LockState.JAMMED)
    await hass.async_block_till_done()
    expect(acc.char_current_state.value).to_be(2)
    expect(acc.char_target_state.value).to_be(0)

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    expect(acc.char_current_state.value).to_be(2)
    expect(acc.char_target_state.value).to_be(0)

    # Unavailable should keep last state but mark accessory unavailable.
    hass.states.async_set(entity_id, STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    expect(acc.char_current_state.value).to_be(2)
    expect(acc.char_target_state.value).to_be(0)
    expect(acc.available).to_be(False)

    hass.states.async_set(entity_id, LockState.UNLOCKED)
    await hass.async_block_till_done()
    expect(acc.char_current_state.value).to_be(0)
    expect(acc.char_target_state.value).to_be(0)
    expect(acc.available).to_be(True)

    hass.states.async_set(entity_id, STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    expect(acc.char_current_state.value).to_be(0)
    expect(acc.char_target_state.value).to_be(0)
    expect(acc.available).to_be(False)

    hass.states.async_remove(entity_id)
    await hass.async_block_till_done()
    expect(acc.char_current_state.value).to_be(0)
    expect(acc.char_target_state.value).to_be(0)

    # Set from HomeKit
    call_lock = async_mock_service(hass, LOCK_DOMAIN, "lock")
    call_unlock = async_mock_service(hass, LOCK_DOMAIN, "unlock")

    acc.char_target_state.client_update_value(1)
    await hass.async_block_till_done()
    expect(bool(call_lock)).to_be(True)
    expect(call_lock[0].data[ATTR_ENTITY_ID]).to_be(entity_id)
    expect(call_lock[0].data[ATTR_CODE]).to_be(code)
    expect(acc.char_target_state.value).to_be(1)
    expect(len(events)).to_be(1)
    expect(events[-1].data[ATTR_VALUE]).to_be(None)

    acc.char_target_state.client_update_value(0)
    await hass.async_block_till_done()
    expect(bool(call_unlock)).to_be(True)
    expect(call_unlock[0].data[ATTR_ENTITY_ID]).to_be(entity_id)
    expect(call_unlock[0].data[ATTR_CODE]).to_be(code)
    expect(acc.char_target_state.value).to_be(0)
    expect(len(events)).to_be(2)
    expect(events[-1].data[ATTR_VALUE]).to_be(None)


@test.cases(
    test.case("empty_config", config={}),
    test.case("none_code", config={ATTR_CODE: None}),
)
async def no_code(
    *,
    config: dict[str, Any],
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
    events: list[Event] = Depends(events_fixture),
) -> None:
    """Test accessory if lock doesn't require a code."""
    entity_id = "lock.kitchen_door"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = Lock(hass, hk_driver, "Lock", entity_id, 2, config)

    # Set from HomeKit
    call_lock = async_mock_service(hass, LOCK_DOMAIN, "lock")

    acc.char_target_state.client_update_value(1)
    await hass.async_block_till_done()
    expect(bool(call_lock)).to_be(True)
    expect(call_lock[0].data[ATTR_ENTITY_ID]).to_be(entity_id)
    expect(ATTR_CODE in call_lock[0].data).to_be(False)
    expect(acc.char_target_state.value).to_be(1)
    expect(len(events)).to_be(1)
    expect(events[-1].data[ATTR_VALUE]).to_be(None)


@test
async def lock_with_linked_doorbell_sensor(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test a lock with a linked doorbell sensor can update."""
    code = "1234"
    await async_setup_component(hass, lock.DOMAIN, {lock.DOMAIN: {"platform": "demo"}})
    await hass.async_block_till_done()
    doorbell_entity_id = "binary_sensor.doorbell"

    hass.states.async_set(
        doorbell_entity_id,
        STATE_ON,
        {ATTR_DEVICE_CLASS: BinarySensorDeviceClass.OCCUPANCY},
    )
    await hass.async_block_till_done()
    entity_id = "lock.demo_lock"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = Lock(
        hass,
        hk_driver,
        "Lock",
        entity_id,
        2,
        {
            ATTR_CODE: code,
            CONF_LINKED_DOORBELL_SENSOR: doorbell_entity_id,
        },
    )
    bridge = HomeBridge("hass", hk_driver, "Test Bridge")
    bridge.add_accessory(acc)

    acc.run()

    expect(acc.aid).to_be(2)
    expect(acc.category).to_be(6)  # DoorLock

    service = acc.get_service(SERV_DOORBELL)
    expect(service is not None).to_be(True)
    char = service.get_characteristic(CHAR_PROGRAMMABLE_SWITCH_EVENT)
    expect(char is not None).to_be(True)

    expect(char.value).to_be(None)

    service2 = acc.get_service(SERV_STATELESS_PROGRAMMABLE_SWITCH)
    expect(service2 is not None).to_be(True)
    char2 = service.get_characteristic(CHAR_PROGRAMMABLE_SWITCH_EVENT)
    expect(char2 is not None).to_be(True)
    broker = MagicMock()
    char2.broker = broker
    expect(char2.value).to_be(None)

    hass.states.async_set(
        doorbell_entity_id,
        STATE_OFF,
        {ATTR_DEVICE_CLASS: BinarySensorDeviceClass.OCCUPANCY},
    )
    await hass.async_block_till_done()
    expect(char.value).to_be(None)
    expect(char2.value).to_be(None)
    expect(len(broker.mock_calls)).to_be(0)

    char.set_value(True)
    char2.set_value(True)
    broker.reset_mock()

    hass.states.async_set(
        doorbell_entity_id,
        STATE_ON,
        {ATTR_DEVICE_CLASS: BinarySensorDeviceClass.OCCUPANCY},
    )
    await hass.async_block_till_done()
    expect(char.value).to_be(None)
    expect(char2.value).to_be(None)
    expect(len(broker.mock_calls)).to_be(2)
    broker.reset_mock()

    hass.states.async_set(
        doorbell_entity_id,
        STATE_ON,
        {ATTR_DEVICE_CLASS: BinarySensorDeviceClass.OCCUPANCY},
        force_update=True,
    )
    await hass.async_block_till_done()
    expect(char.value).to_be(None)
    expect(char2.value).to_be(None)
    expect(len(broker.mock_calls)).to_be(0)
    broker.reset_mock()

    hass.states.async_set(
        doorbell_entity_id,
        STATE_ON,
        {ATTR_DEVICE_CLASS: BinarySensorDeviceClass.OCCUPANCY, "other": "attr"},
    )
    await hass.async_block_till_done()
    expect(char.value).to_be(None)
    expect(char2.value).to_be(None)
    expect(len(broker.mock_calls)).to_be(0)
    broker.reset_mock()

    # Ensure removing the linked doorbell sensor does not throw.
    hass.states.async_remove(doorbell_entity_id)
    await hass.async_block_till_done()
    acc.run()
    await hass.async_block_till_done()
    expect(char.value).to_be(None)
    expect(char2.value).to_be(None)


@test
async def lock_with_linked_doorbell_event(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test a lock with a linked doorbell event can update."""
    await async_setup_component(hass, lock.DOMAIN, {lock.DOMAIN: {"platform": "demo"}})
    await hass.async_block_till_done()
    doorbell_entity_id = "event.doorbell"
    code = "1234"

    hass.states.async_set(
        doorbell_entity_id,
        dt_util.utcnow().isoformat(),
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL},
    )
    await hass.async_block_till_done()
    entity_id = "lock.demo_lock"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = Lock(
        hass,
        hk_driver,
        "Lock",
        entity_id,
        2,
        {
            ATTR_CODE: code,
            CONF_LINKED_DOORBELL_SENSOR: doorbell_entity_id,
        },
    )
    bridge = HomeBridge("hass", hk_driver, "Test Bridge")
    bridge.add_accessory(acc)

    acc.run()

    expect(acc.aid).to_be(2)
    expect(acc.category).to_be(6)  # DoorLock

    service = acc.get_service(SERV_DOORBELL)
    expect(service is not None).to_be(True)
    char = service.get_characteristic(CHAR_PROGRAMMABLE_SWITCH_EVENT)
    expect(char is not None).to_be(True)

    expect(char.value).to_be(None)

    service2 = acc.get_service(SERV_STATELESS_PROGRAMMABLE_SWITCH)
    expect(service2 is not None).to_be(True)
    char2 = service.get_characteristic(CHAR_PROGRAMMABLE_SWITCH_EVENT)
    expect(char2 is not None).to_be(True)
    broker = MagicMock()
    char2.broker = broker
    expect(char2.value).to_be(None)

    hass.states.async_set(
        doorbell_entity_id,
        STATE_UNKNOWN,
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL},
    )
    await hass.async_block_till_done()
    expect(char.value).to_be(None)
    expect(char2.value).to_be(None)
    expect(len(broker.mock_calls)).to_be(0)

    char.set_value(True)
    char2.set_value(True)
    broker.reset_mock()

    original_time = dt_util.utcnow().isoformat()
    hass.states.async_set(
        doorbell_entity_id,
        original_time,
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL},
    )
    await hass.async_block_till_done()
    expect(char.value).to_be(None)
    expect(char2.value).to_be(None)
    expect(len(broker.mock_calls)).to_be(2)
    broker.reset_mock()

    hass.states.async_set(
        doorbell_entity_id,
        original_time,
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL},
        force_update=True,
    )
    await hass.async_block_till_done()
    expect(char.value).to_be(None)
    expect(char2.value).to_be(None)
    expect(len(broker.mock_calls)).to_be(0)
    broker.reset_mock()

    hass.states.async_set(
        doorbell_entity_id,
        original_time,
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL, "other": "attr"},
    )
    await hass.async_block_till_done()
    expect(char.value).to_be(None)
    expect(char2.value).to_be(None)
    expect(len(broker.mock_calls)).to_be(0)
    broker.reset_mock()

    # Ensure removing the linked doorbell sensor does not throw.
    hass.states.async_remove(doorbell_entity_id)
    await hass.async_block_till_done()
    acc.run()
    await hass.async_block_till_done()
    expect(char.value).to_be(None)
    expect(char2.value).to_be(None)

    await hass.async_block_till_done()
    hass.states.async_set(
        doorbell_entity_id,
        STATE_UNAVAILABLE,
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL},
    )
    await hass.async_block_till_done()
    # Re-adding should not fire an event.
    expect(bool(broker.mock_calls)).to_be(False)
    broker.reset_mock()

    # Going from unavailable to a state should not fire an event.
    hass.states.async_set(
        doorbell_entity_id,
        dt_util.utcnow().isoformat(),
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL},
    )
    await hass.async_block_till_done()
    expect(bool(broker.mock_calls)).to_be(False)

    # But a second update does.
    hass.states.async_set(
        doorbell_entity_id,
        dt_util.utcnow().isoformat(),
        {ATTR_DEVICE_CLASS: EventDeviceClass.DOORBELL},
    )
    await hass.async_block_till_done()
    expect(bool(broker.mock_calls)).to_be(True)


@test
async def lock_with_a_missing_linked_doorbell_sensor(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test a lock with a configured linked doorbell sensor that is missing."""
    await async_setup_component(hass, lock.DOMAIN, {lock.DOMAIN: {"platform": "demo"}})
    await hass.async_block_till_done()
    code = "1234"
    doorbell_entity_id = "binary_sensor.doorbell"
    entity_id = "lock.demo_lock"
    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = Lock(
        hass,
        hk_driver,
        "Lock",
        entity_id,
        2,
        {
            ATTR_CODE: code,
            CONF_LINKED_DOORBELL_SENSOR: doorbell_entity_id,
        },
    )
    bridge = HomeBridge("hass", hk_driver, "Test Bridge")
    bridge.add_accessory(acc)

    acc.run()

    expect(acc.aid).to_be(2)
    expect(acc.category).to_be(6)  # DoorLock

    expect(bool(acc.get_service(SERV_DOORBELL))).to_be(False)
    expect(bool(acc.get_service(SERV_STATELESS_PROGRAMMABLE_SWITCH))).to_be(False)
