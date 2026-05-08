"""Test different accessory types: Security Systems (tryke port)."""

from __future__ import annotations

from typing import Any

from pyhap.loader import get_loader
from tryke import Depends, expect, fixture, test

from homeassistant.components.alarm_control_panel import (
    DOMAIN as ALARM_CONTROL_PANEL_DOMAIN,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.components.homekit.accessories import HomeDriver
from homeassistant.components.homekit.const import ATTR_VALUE
from homeassistant.components.homekit.type_security_systems import SecuritySystem
from homeassistant.const import (
    ATTR_CODE,
    ATTR_ENTITY_ID,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant

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
async def switch_set_state(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
    events: list[Event] = Depends(events_fixture),
) -> None:
    """Test if accessory and HA are updated accordingly."""
    code = "1234"
    config = {ATTR_CODE: code}
    entity_id = "alarm_control_panel.test"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = SecuritySystem(hass, hk_driver, "SecuritySystem", entity_id, 2, config)
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_be(2)
    expect(acc.category).to_be(11)  # AlarmSystem

    expect(acc.char_current_state.value).to_be(3)
    expect(acc.char_target_state.value).to_be(3)

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_AWAY)
    await hass.async_block_till_done()
    expect(acc.char_target_state.value).to_be(1)
    expect(acc.char_current_state.value).to_be(1)

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_HOME)
    await hass.async_block_till_done()
    expect(acc.char_target_state.value).to_be(0)
    expect(acc.char_current_state.value).to_be(0)

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_NIGHT)
    await hass.async_block_till_done()
    expect(acc.char_target_state.value).to_be(2)
    expect(acc.char_current_state.value).to_be(2)

    hass.states.async_set(entity_id, AlarmControlPanelState.DISARMED)
    await hass.async_block_till_done()
    expect(acc.char_target_state.value).to_be(3)
    expect(acc.char_current_state.value).to_be(3)

    hass.states.async_set(entity_id, AlarmControlPanelState.TRIGGERED)
    await hass.async_block_till_done()
    expect(acc.char_target_state.value).to_be(3)
    expect(acc.char_current_state.value).to_be(4)

    hass.states.async_set(entity_id, STATE_UNKNOWN)
    await hass.async_block_till_done()
    expect(acc.char_target_state.value).to_be(3)
    expect(acc.char_current_state.value).to_be(4)

    # Set from HomeKit
    call_arm_home = async_mock_service(
        hass, ALARM_CONTROL_PANEL_DOMAIN, "alarm_arm_home"
    )
    call_arm_away = async_mock_service(
        hass, ALARM_CONTROL_PANEL_DOMAIN, "alarm_arm_away"
    )
    call_arm_night = async_mock_service(
        hass, ALARM_CONTROL_PANEL_DOMAIN, "alarm_arm_night"
    )
    call_disarm = async_mock_service(hass, ALARM_CONTROL_PANEL_DOMAIN, "alarm_disarm")

    acc.char_target_state.client_update_value(0)
    await hass.async_block_till_done()
    expect(bool(call_arm_home)).to_be(True)
    expect(call_arm_home[0].data[ATTR_ENTITY_ID]).to_be(entity_id)
    expect(call_arm_home[0].data[ATTR_CODE]).to_be(code)
    expect(acc.char_target_state.value).to_be(0)
    expect(len(events)).to_be(1)
    expect(events[-1].data[ATTR_VALUE]).to_be(None)

    acc.char_target_state.client_update_value(1)
    await hass.async_block_till_done()
    expect(bool(call_arm_away)).to_be(True)
    expect(call_arm_away[0].data[ATTR_ENTITY_ID]).to_be(entity_id)
    expect(call_arm_away[0].data[ATTR_CODE]).to_be(code)
    expect(acc.char_target_state.value).to_be(1)
    expect(len(events)).to_be(2)
    expect(events[-1].data[ATTR_VALUE]).to_be(None)

    acc.char_target_state.client_update_value(2)
    await hass.async_block_till_done()
    expect(bool(call_arm_night)).to_be(True)
    expect(call_arm_night[0].data[ATTR_ENTITY_ID]).to_be(entity_id)
    expect(call_arm_night[0].data[ATTR_CODE]).to_be(code)
    expect(acc.char_target_state.value).to_be(2)
    expect(len(events)).to_be(3)
    expect(events[-1].data[ATTR_VALUE]).to_be(None)

    acc.char_target_state.client_update_value(3)
    await hass.async_block_till_done()
    expect(bool(call_disarm)).to_be(True)
    expect(call_disarm[0].data[ATTR_ENTITY_ID]).to_be(entity_id)
    expect(call_disarm[0].data[ATTR_CODE]).to_be(code)
    expect(acc.char_target_state.value).to_be(3)
    expect(len(events)).to_be(4)
    expect(events[-1].data[ATTR_VALUE]).to_be(None)


@test.cases(
    test.case("empty_config", config={}),
    test.case("none_code", config={ATTR_CODE: None}),
)
async def no_alarm_code(
    *,
    config: dict[str, Any],
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
    events: list[Event] = Depends(events_fixture),
) -> None:
    """Test accessory if security_system doesn't require an alarm_code."""
    entity_id = "alarm_control_panel.test"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = SecuritySystem(hass, hk_driver, "SecuritySystem", entity_id, 2, config)

    # Set from HomeKit
    call_arm_home = async_mock_service(
        hass, ALARM_CONTROL_PANEL_DOMAIN, "alarm_arm_home"
    )

    acc.char_target_state.client_update_value(0)
    await hass.async_block_till_done()
    expect(bool(call_arm_home)).to_be(True)
    expect(call_arm_home[0].data[ATTR_ENTITY_ID]).to_be(entity_id)
    expect(ATTR_CODE in call_arm_home[0].data).to_be(False)
    expect(acc.char_target_state.value).to_be(0)
    expect(len(events)).to_be(1)
    expect(events[-1].data[ATTR_VALUE]).to_be(None)


@test
async def arming(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test to make sure arming sets the right state."""
    entity_id = "alarm_control_panel.test"

    hass.states.async_set(entity_id, None)

    acc = SecuritySystem(hass, hk_driver, "SecuritySystem", entity_id, 2, {})
    acc.run()
    await hass.async_block_till_done()

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_AWAY)
    await hass.async_block_till_done()
    expect(acc.char_target_state.value).to_be(1)
    expect(acc.char_current_state.value).to_be(1)

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_HOME)
    await hass.async_block_till_done()
    expect(acc.char_target_state.value).to_be(0)
    expect(acc.char_current_state.value).to_be(0)

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_VACATION)
    await hass.async_block_till_done()
    expect(acc.char_target_state.value).to_be(1)
    expect(acc.char_current_state.value).to_be(1)

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_NIGHT)
    await hass.async_block_till_done()
    expect(acc.char_target_state.value).to_be(2)
    expect(acc.char_current_state.value).to_be(2)

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMING)
    await hass.async_block_till_done()
    expect(acc.char_target_state.value).to_be(1)
    expect(acc.char_current_state.value).to_be(3)

    hass.states.async_set(entity_id, AlarmControlPanelState.DISARMED)
    await hass.async_block_till_done()
    expect(acc.char_target_state.value).to_be(3)
    expect(acc.char_current_state.value).to_be(3)

    hass.states.async_set(entity_id, AlarmControlPanelState.ARMED_AWAY)
    await hass.async_block_till_done()
    expect(acc.char_target_state.value).to_be(1)
    expect(acc.char_current_state.value).to_be(1)

    hass.states.async_set(entity_id, AlarmControlPanelState.TRIGGERED)
    await hass.async_block_till_done()
    expect(acc.char_target_state.value).to_be(1)
    expect(acc.char_current_state.value).to_be(4)


@test
async def supported_states(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test different supported states."""
    code = "1234"
    config = {ATTR_CODE: code}
    entity_id = "alarm_control_panel.test"

    loader = get_loader()
    default_current_states = loader.get_char(
        "SecuritySystemCurrentState"
    ).properties.get("ValidValues")
    default_target_services = loader.get_char(
        "SecuritySystemTargetState"
    ).properties.get("ValidValues")

    test_configs: list[dict[str, Any]] = [
        {
            "features": AlarmControlPanelEntityFeature.ARM_HOME,
            "current_values": [
                default_current_states["Disarmed"],
                default_current_states["AlarmTriggered"],
                default_current_states["StayArm"],
            ],
            "target_values": [
                default_target_services["Disarm"],
                default_target_services["StayArm"],
            ],
        },
        {
            "features": AlarmControlPanelEntityFeature.ARM_AWAY,
            "current_values": [
                default_current_states["Disarmed"],
                default_current_states["AlarmTriggered"],
                default_current_states["AwayArm"],
            ],
            "target_values": [
                default_target_services["Disarm"],
                default_target_services["AwayArm"],
            ],
        },
        {
            "features": AlarmControlPanelEntityFeature.ARM_HOME
            | AlarmControlPanelEntityFeature.ARM_AWAY,
            "current_values": [
                default_current_states["Disarmed"],
                default_current_states["AlarmTriggered"],
                default_current_states["StayArm"],
                default_current_states["AwayArm"],
            ],
            "target_values": [
                default_target_services["Disarm"],
                default_target_services["StayArm"],
                default_target_services["AwayArm"],
            ],
        },
        {
            "features": AlarmControlPanelEntityFeature.ARM_HOME
            | AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_NIGHT,
            "current_values": [
                default_current_states["Disarmed"],
                default_current_states["AlarmTriggered"],
                default_current_states["StayArm"],
                default_current_states["AwayArm"],
                default_current_states["NightArm"],
            ],
            "target_values": [
                default_target_services["Disarm"],
                default_target_services["StayArm"],
                default_target_services["AwayArm"],
                default_target_services["NightArm"],
            ],
        },
        {
            "features": AlarmControlPanelEntityFeature.ARM_HOME
            | AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_NIGHT
            | AlarmControlPanelEntityFeature.TRIGGER,
            "current_values": [
                default_current_states["Disarmed"],
                default_current_states["AlarmTriggered"],
                default_current_states["StayArm"],
                default_current_states["AwayArm"],
                default_current_states["NightArm"],
            ],
            "target_values": [
                default_target_services["Disarm"],
                default_target_services["StayArm"],
                default_target_services["AwayArm"],
                default_target_services["NightArm"],
            ],
        },
    ]

    aid = 1

    for test_config in test_configs:
        attrs = {"supported_features": test_config.get("features")}

        hass.states.async_set(entity_id, None, attributes=attrs)
        await hass.async_block_till_done()

        aid += 1
        acc = SecuritySystem(hass, hk_driver, "SecuritySystem", entity_id, aid, config)
        acc.run()
        await hass.async_block_till_done()

        valid_current_values = acc.char_current_state.properties.get("ValidValues")
        valid_target_values = acc.char_target_state.properties.get("ValidValues")

        for val in valid_current_values.values():
            expect(val in test_config.get("current_values")).to_be(True)

        for val in valid_target_values.values():
            expect(val in test_config.get("target_values")).to_be(True)


@test.cases(
    test.case("none", state=None),
    test.case("string_none", state="None"),
    test.case("unknown", state=STATE_UNKNOWN),
    test.case("unavailable", state=STATE_UNAVAILABLE),
)
async def handle_non_alarm_states(
    *,
    state: str | None,
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
    events: list[Event] = Depends(events_fixture),
) -> None:
    """Test we can handle states that should not raise."""
    del events
    code = "1234"
    config = {ATTR_CODE: code}
    entity_id = "alarm_control_panel.test"

    hass.states.async_set(entity_id, state)
    await hass.async_block_till_done()
    acc = SecuritySystem(hass, hk_driver, "SecuritySystem", entity_id, 2, config)
    acc.run()
    await hass.async_block_till_done()

    expect(acc.aid).to_be(2)
    expect(acc.category).to_be(11)  # AlarmSystem

    expect(acc.char_current_state.value).to_be(3)
    expect(acc.char_target_state.value).to_be(3)
