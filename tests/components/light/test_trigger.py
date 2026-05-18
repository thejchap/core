"""Test light trigger."""

from typing import Any

from tryke import Depends, fixture, test

from homeassistant.components.light import ATTR_BRIGHTNESS
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant

from ._fixtures import (
    enable_labs_preview_features,
    target_lights as target_lights_fixture,
)

from tests.components.common import (
    TriggerStateDescription,
    assert_trigger_behavior_any,
    assert_trigger_behavior_first,
    assert_trigger_behavior_last,
    assert_trigger_gated_by_labs_flag,
    assert_trigger_ignores_limit_entities_with_wrong_unit,
    assert_trigger_options_supported,
    parametrize_numerical_attribute_changed_trigger_states,
    parametrize_numerical_attribute_crossed_threshold_trigger_states,
    parametrize_target_entities,
    parametrize_trigger_states,
)
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)

# Brightness is stored as a uint8 (0-255) but the trigger threshold is in
# percent (0-100). The generic numerical-attribute helpers feed values in
# the threshold's percent space and scale them by `attribute_value_scale`
# to land on the entity's storage values; for brightness that's
# 255/100 = 2.55 (so 0/50/60/100 -> 0/127.5/153/255).
_BRIGHTNESS_VALUE_SCALE = 255 / 100


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    return 0


@test.cases(
    test.case("brightness_changed", trigger_key="light.brightness_changed"),
    test.case(
        "brightness_crossed_threshold",
        trigger_key="light.brightness_crossed_threshold",
    ),
    test.case("turned_off", trigger_key="light.turned_off"),
    test.case("turned_on", trigger_key="light.turned_on"),
)
async def light_triggers_gated_by_labs_flag(
    trigger_key: str,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the light triggers are gated by the labs flag."""
    await assert_trigger_gated_by_labs_flag(hass, caplog, trigger_key)


@test.cases(
    test.case(
        "turned_on",
        trigger_key="light.turned_on",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "turned_off",
        trigger_key="light.turned_off",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
)
async def light_trigger_options_validation(
    trigger_key: str,
    base_options: dict[str, Any] | None,
    supports_behavior: bool,
    supports_duration: bool,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that light triggers support the expected options."""
    await assert_trigger_options_supported(
        hass,
        trigger_key,
        base_options,
        supports_behavior=supports_behavior,
        supports_duration=supports_duration,
    )


_LIGHT_TARGET_PARAMS = parametrize_target_entities("light")

_STATE_TRIGGER_STATES = [
    *parametrize_trigger_states(
        trigger="light.turned_on",
        target_states=[STATE_ON],
        other_states=[STATE_OFF],
    ),
    *parametrize_trigger_states(
        trigger="light.turned_off",
        target_states=[STATE_OFF],
        other_states=[STATE_ON],
    ),
]

_ATTRIBUTE_BEHAVIOR_ANY_STATES = [
    *parametrize_numerical_attribute_changed_trigger_states(
        "light.brightness_changed",
        STATE_ON,
        ATTR_BRIGHTNESS,
        attribute_value_scale=_BRIGHTNESS_VALUE_SCALE,
    ),
    *parametrize_numerical_attribute_crossed_threshold_trigger_states(
        "light.brightness_crossed_threshold",
        STATE_ON,
        ATTR_BRIGHTNESS,
        attribute_value_scale=_BRIGHTNESS_VALUE_SCALE,
    ),
]

_ATTRIBUTE_CROSSED_STATES = [
    *parametrize_numerical_attribute_crossed_threshold_trigger_states(
        "light.brightness_crossed_threshold",
        STATE_ON,
        ATTR_BRIGHTNESS,
        attribute_value_scale=_BRIGHTNESS_VALUE_SCALE,
    ),
]


@test
async def light_state_trigger_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_lights: dict[str, list[str]] = Depends(target_lights_fixture),
) -> None:
    """Test the light state trigger fires when any light state changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _LIGHT_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_TRIGGER_STATES:
            await assert_trigger_behavior_any(
                hass,
                target_entities=target_lights,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def light_state_attribute_trigger_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_lights: dict[str, list[str]] = Depends(target_lights_fixture),
) -> None:
    """Test the light attribute trigger fires when any light state changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _LIGHT_TARGET_PARAMS:
        for trigger, trigger_options, states in _ATTRIBUTE_BEHAVIOR_ANY_STATES:
            await assert_trigger_behavior_any(
                hass,
                target_entities=target_lights,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def light_state_trigger_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_lights: dict[str, list[str]] = Depends(target_lights_fixture),
) -> None:
    """Test the light state trigger fires when the first light changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _LIGHT_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_TRIGGER_STATES:
            await assert_trigger_behavior_first(
                hass,
                target_entities=target_lights,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def light_state_attribute_trigger_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_lights: dict[str, list[str]] = Depends(target_lights_fixture),
) -> None:
    """Test the light attribute trigger fires when the first light state changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _LIGHT_TARGET_PARAMS:
        for trigger, trigger_options, states in _ATTRIBUTE_CROSSED_STATES:
            await assert_trigger_behavior_first(
                hass,
                target_entities=target_lights,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def light_state_trigger_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_lights: dict[str, list[str]] = Depends(target_lights_fixture),
) -> None:
    """Test the light state trigger fires when the last light changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _LIGHT_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_TRIGGER_STATES:
            await assert_trigger_behavior_last(
                hass,
                target_entities=target_lights,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def light_state_attribute_trigger_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_lights: dict[str, list[str]] = Depends(target_lights_fixture),
) -> None:
    """Test the light attribute trigger fires when the last light state changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _LIGHT_TARGET_PARAMS:
        for trigger, trigger_options, states in _ATTRIBUTE_CROSSED_STATES:
            await assert_trigger_behavior_last(
                hass,
                target_entities=target_lights,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test.cases(
    test.case(
        "brightness_changed",
        trigger="light.brightness_changed",
        trigger_options={
            "threshold": {
                "type": "between",
                "value_min": {"entity": "sensor.brightness_above"},
                "value_max": {"entity": "sensor.brightness_below"},
            },
        },
        limit_entities=["sensor.brightness_above", "sensor.brightness_below"],
    ),
    test.case(
        "brightness_crossed_threshold",
        trigger="light.brightness_crossed_threshold",
        trigger_options={
            "threshold": {
                "type": "between",
                "value_min": {"entity": "sensor.brightness_lower"},
                "value_max": {"entity": "sensor.brightness_upper"},
            },
        },
        limit_entities=["sensor.brightness_lower", "sensor.brightness_upper"],
    ),
)
async def light_trigger_ignores_limit_entity_with_wrong_unit(
    trigger: str,
    trigger_options: dict[str, Any],
    limit_entities: list[str],
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test numerical triggers do not fire if limit entities have the wrong unit."""
    await assert_trigger_ignores_limit_entities_with_wrong_unit(
        hass,
        trigger=trigger,
        trigger_options=trigger_options,
        entity_id="light.test_light",
        reset_state={"state": STATE_ON, "attributes": {ATTR_BRIGHTNESS: 0}},
        trigger_state={"state": STATE_ON, "attributes": {ATTR_BRIGHTNESS: 128}},
        limit_entities=[
            (limit_entities[0], "10"),
            (limit_entities[1], "90"),
        ],
        correct_unit="%",
        wrong_unit="lx",
    )


# Silence unused-import warning — TriggerStateDescription is part of the
# public test surface used by these helpers but not directly referenced.
_ = TriggerStateDescription
