"""Test switch triggers."""

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.switch import DOMAIN
from homeassistant.const import CONF_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant

from ._fixtures import (
    enable_labs_preview_features,
    target_input_booleans as target_input_booleans_fixture,
    target_switches as target_switches_fixture,
)

from tests.components.common import (
    TriggerStateDescription,
    arm_trigger,
    assert_trigger_behavior_any,
    assert_trigger_behavior_first,
    assert_trigger_behavior_last,
    assert_trigger_gated_by_labs_flag,
    assert_trigger_options_supported,
    parametrize_target_entities,
    parametrize_trigger_states,
)
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    return 0


TRIGGER_STATES = [
    *parametrize_trigger_states(
        trigger="switch.turned_off",
        target_states=[STATE_OFF],
        other_states=[STATE_ON],
    ),
    *parametrize_trigger_states(
        trigger="switch.turned_on",
        target_states=[STATE_ON],
        other_states=[STATE_OFF],
    ),
]

_SWITCH_TARGET_PARAMS = parametrize_target_entities(DOMAIN)
_INPUT_BOOLEAN_TARGET_PARAMS = parametrize_target_entities("input_boolean")


@test.cases(
    test.case("turned_off", trigger_key="switch.turned_off"),
    test.case("turned_on", trigger_key="switch.turned_on"),
)
async def switch_triggers_gated_by_labs_flag(
    trigger_key: str,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the switch triggers are gated by the labs flag."""
    await assert_trigger_gated_by_labs_flag(hass, caplog, trigger_key)


@test.cases(
    test.case(
        "turned_off",
        trigger_key="switch.turned_off",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "turned_on",
        trigger_key="switch.turned_on",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
)
async def switch_trigger_options_validation(
    trigger_key: str,
    base_options: dict[str, Any] | None,
    supports_behavior: bool,
    supports_duration: bool,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that switch triggers support the expected options."""
    await assert_trigger_options_supported(
        hass,
        trigger_key,
        base_options,
        supports_behavior=supports_behavior,
        supports_duration=supports_duration,
    )


# --- Switch domain tests ---


@test
async def switch_state_trigger_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_switches: dict[str, list[str]] = Depends(target_switches_fixture),
) -> None:
    """Test that the switch state trigger fires when any switch state changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _SWITCH_TARGET_PARAMS:
        for trigger, trigger_options, states in TRIGGER_STATES:
            await assert_trigger_behavior_any(
                hass,
                target_entities=target_switches,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def switch_state_trigger_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_switches: dict[str, list[str]] = Depends(target_switches_fixture),
) -> None:
    """Test that the switch state trigger fires when the first switch changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _SWITCH_TARGET_PARAMS:
        for trigger, trigger_options, states in TRIGGER_STATES:
            await assert_trigger_behavior_first(
                hass,
                target_entities=target_switches,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def switch_state_trigger_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_switches: dict[str, list[str]] = Depends(target_switches_fixture),
) -> None:
    """Test that the switch state trigger fires when the last switch changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _SWITCH_TARGET_PARAMS:
        for trigger, trigger_options, states in TRIGGER_STATES:
            await assert_trigger_behavior_last(
                hass,
                target_entities=target_switches,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


# --- Input boolean domain tests ---


@test
async def input_boolean_state_trigger_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_input_booleans: dict[str, list[str]] = Depends(target_input_booleans_fixture),
) -> None:
    """Test that the switch trigger fires when any input_boolean state changes."""
    for trigger_target_config, entity_id, entities_in_target in _INPUT_BOOLEAN_TARGET_PARAMS:
        for trigger, trigger_options, states in TRIGGER_STATES:
            await assert_trigger_behavior_any(
                hass,
                target_entities=target_input_booleans,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def input_boolean_state_trigger_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_input_booleans: dict[str, list[str]] = Depends(target_input_booleans_fixture),
) -> None:
    """Test that the switch trigger fires when the first input_boolean changes."""
    for trigger_target_config, entity_id, entities_in_target in _INPUT_BOOLEAN_TARGET_PARAMS:
        for trigger, trigger_options, states in TRIGGER_STATES:
            await assert_trigger_behavior_first(
                hass,
                target_entities=target_input_booleans,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def input_boolean_state_trigger_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_input_booleans: dict[str, list[str]] = Depends(target_input_booleans_fixture),
) -> None:
    """Test that the switch trigger fires when the last input_boolean changes."""
    for trigger_target_config, entity_id, entities_in_target in _INPUT_BOOLEAN_TARGET_PARAMS:
        for trigger, trigger_options, states in TRIGGER_STATES:
            await assert_trigger_behavior_last(
                hass,
                target_entities=target_input_booleans,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


# --- Cross-domain test ---


@test
async def switch_trigger_fires_for_both_domains(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that the switch trigger fires for both switch and input_boolean entities."""
    calls: list[str] = []
    entity_id_switch = "switch.test_switch"
    entity_id_input_boolean = "input_boolean.test_input_boolean"

    hass.states.async_set(entity_id_switch, STATE_OFF)
    hass.states.async_set(entity_id_input_boolean, STATE_OFF)
    await hass.async_block_till_done()

    await arm_trigger(
        hass,
        "switch.turned_on",
        {},
        {CONF_ENTITY_ID: [entity_id_switch, entity_id_input_boolean]},
        calls,
    )

    # switch entity changes - should trigger
    hass.states.async_set(entity_id_switch, STATE_ON)
    await hass.async_block_till_done()
    expect(calls).to_have_length(1)
    expect(calls[0]).to_equal(entity_id_switch)
    calls.clear()

    # input_boolean entity changes - should also trigger
    hass.states.async_set(entity_id_input_boolean, STATE_ON)
    await hass.async_block_till_done()
    expect(calls).to_have_length(1)
    expect(calls[0]).to_equal(entity_id_input_boolean)
    calls.clear()


# Silence unused-import warning — TriggerStateDescription is part of the
# public test surface used by these helpers but not directly referenced.
_ = TriggerStateDescription
