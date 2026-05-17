"""Test moisture trigger."""

from typing import Any

from tryke import Depends, fixture, test

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant

from ._fixtures import (
    enable_labs_preview_features,
    target_binary_sensors as target_binary_sensors_fixture,
    target_sensors as target_sensors_fixture,
)

from tests.components.common import (
    TriggerStateDescription,
    assert_trigger_behavior_any,
    assert_trigger_behavior_first,
    assert_trigger_behavior_last,
    assert_trigger_gated_by_labs_flag,
    assert_trigger_ignores_limit_entities_with_wrong_unit,
    assert_trigger_options_supported,
    parametrize_numerical_state_value_changed_trigger_states,
    parametrize_numerical_state_value_crossed_threshold_trigger_states,
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


@test.cases(
    test.case("detected", trigger_key="moisture.detected"),
    test.case("cleared", trigger_key="moisture.cleared"),
    test.case("changed", trigger_key="moisture.changed"),
    test.case("crossed_threshold", trigger_key="moisture.crossed_threshold"),
)
async def moisture_triggers_gated_by_labs_flag(
    trigger_key: str,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the moisture triggers are gated by the labs flag."""
    await assert_trigger_gated_by_labs_flag(hass, caplog, trigger_key)


@test.cases(
    test.case(
        "detected",
        trigger_key="moisture.detected",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "cleared",
        trigger_key="moisture.cleared",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
)
async def moisture_trigger_options_validation(
    trigger_key: str,
    base_options: dict[str, Any] | None,
    supports_behavior: bool,
    supports_duration: bool,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that moisture triggers support the expected options."""
    await assert_trigger_options_supported(
        hass,
        trigger_key,
        base_options,
        supports_behavior=supports_behavior,
        supports_duration=supports_duration,
    )


# --- Binary sensor domain tests ---


_BINARY_SENSOR_TARGET_PARAMS = parametrize_target_entities("binary_sensor")
_SENSOR_TARGET_PARAMS = parametrize_target_entities("sensor")

_BINARY_SENSOR_STATES = [
    *parametrize_trigger_states(
        trigger="moisture.detected",
        target_states=[STATE_ON],
        other_states=[STATE_OFF],
        required_filter_attributes={
            ATTR_DEVICE_CLASS: BinarySensorDeviceClass.MOISTURE
        },
        trigger_from_none=False,
    ),
    *parametrize_trigger_states(
        trigger="moisture.cleared",
        target_states=[STATE_OFF],
        other_states=[STATE_ON],
        required_filter_attributes={
            ATTR_DEVICE_CLASS: BinarySensorDeviceClass.MOISTURE
        },
        trigger_from_none=False,
    ),
]

_SENSOR_BEHAVIOR_ANY_STATES = [
    *parametrize_numerical_state_value_changed_trigger_states(
        "moisture.changed",
        device_class=SensorDeviceClass.MOISTURE,
        unit_attributes={ATTR_UNIT_OF_MEASUREMENT: "%"},
    ),
    *parametrize_numerical_state_value_crossed_threshold_trigger_states(
        "moisture.crossed_threshold",
        device_class=SensorDeviceClass.MOISTURE,
        unit_attributes={ATTR_UNIT_OF_MEASUREMENT: "%"},
    ),
]

_SENSOR_CROSSED_STATES = [
    *parametrize_numerical_state_value_crossed_threshold_trigger_states(
        "moisture.crossed_threshold",
        device_class=SensorDeviceClass.MOISTURE,
        unit_attributes={ATTR_UNIT_OF_MEASUREMENT: "%"},
    ),
]


@test
async def moisture_trigger_binary_sensor_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_binary_sensors: dict[str, list[str]] = Depends(target_binary_sensors_fixture),
) -> None:
    """Test moisture trigger fires for binary_sensor entities with device_class moisture."""
    for trigger_target_config, entity_id, entities_in_target in _BINARY_SENSOR_TARGET_PARAMS:
        for trigger, trigger_options, states in _BINARY_SENSOR_STATES:
            await assert_trigger_behavior_any(
                hass,
                target_entities=target_binary_sensors,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def moisture_trigger_binary_sensor_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_binary_sensors: dict[str, list[str]] = Depends(target_binary_sensors_fixture),
) -> None:
    """Test moisture trigger fires on the first binary_sensor state change."""
    for trigger_target_config, entity_id, entities_in_target in _BINARY_SENSOR_TARGET_PARAMS:
        for trigger, trigger_options, states in _BINARY_SENSOR_STATES:
            await assert_trigger_behavior_first(
                hass,
                target_entities=target_binary_sensors,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def moisture_trigger_binary_sensor_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_binary_sensors: dict[str, list[str]] = Depends(target_binary_sensors_fixture),
) -> None:
    """Test moisture trigger fires when the last binary_sensor changes state."""
    for trigger_target_config, entity_id, entities_in_target in _BINARY_SENSOR_TARGET_PARAMS:
        for trigger, trigger_options, states in _BINARY_SENSOR_STATES:
            await assert_trigger_behavior_last(
                hass,
                target_entities=target_binary_sensors,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


# --- Sensor domain tests (value in state.state) ---


@test
async def moisture_trigger_sensor_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_sensors: dict[str, list[str]] = Depends(target_sensors_fixture),
) -> None:
    """Test moisture trigger fires for sensor entities with device_class moisture."""
    for trigger_target_config, entity_id, entities_in_target in _SENSOR_TARGET_PARAMS:
        for trigger, trigger_options, states in _SENSOR_BEHAVIOR_ANY_STATES:
            await assert_trigger_behavior_any(
                hass,
                target_entities=target_sensors,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def moisture_trigger_sensor_crossed_threshold_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_sensors: dict[str, list[str]] = Depends(target_sensors_fixture),
) -> None:
    """Test moisture crossed_threshold trigger fires on the first sensor state change."""
    for trigger_target_config, entity_id, entities_in_target in _SENSOR_TARGET_PARAMS:
        for trigger, trigger_options, states in _SENSOR_CROSSED_STATES:
            await assert_trigger_behavior_first(
                hass,
                target_entities=target_sensors,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def moisture_trigger_sensor_crossed_threshold_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_sensors: dict[str, list[str]] = Depends(target_sensors_fixture),
) -> None:
    """Test moisture crossed_threshold trigger fires when the last sensor changes state."""
    for trigger_target_config, entity_id, entities_in_target in _SENSOR_TARGET_PARAMS:
        for trigger, trigger_options, states in _SENSOR_CROSSED_STATES:
            await assert_trigger_behavior_last(
                hass,
                target_entities=target_sensors,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test.cases(
    test.case(
        "changed",
        trigger="moisture.changed",
        trigger_options={
            "threshold": {
                "type": "between",
                "value_min": {"entity": "sensor.moisture_above"},
                "value_max": {"entity": "sensor.moisture_below"},
            },
        },
        limit_entities=["sensor.moisture_above", "sensor.moisture_below"],
    ),
    test.case(
        "crossed_threshold",
        trigger="moisture.crossed_threshold",
        trigger_options={
            "threshold": {
                "type": "between",
                "value_min": {"entity": "sensor.moisture_lower"},
                "value_max": {"entity": "sensor.moisture_upper"},
            },
        },
        limit_entities=["sensor.moisture_lower", "sensor.moisture_upper"],
    ),
)
async def moisture_trigger_ignores_limit_entity_with_wrong_unit(
    trigger: str,
    trigger_options: dict[str, Any],
    limit_entities: list[str],
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test numerical triggers do not fire if limit entities have the wrong unit."""
    moisture_attrs = {
        ATTR_DEVICE_CLASS: SensorDeviceClass.MOISTURE,
        ATTR_UNIT_OF_MEASUREMENT: "%",
    }
    await assert_trigger_ignores_limit_entities_with_wrong_unit(
        hass,
        trigger=trigger,
        trigger_options=trigger_options,
        entity_id="sensor.test_moisture",
        reset_state={"state": "0", "attributes": moisture_attrs},
        trigger_state={"state": "50", "attributes": moisture_attrs},
        limit_entities=[
            (limit_entities[0], "10"),
            (limit_entities[1], "90"),
        ],
        correct_unit="%",
        wrong_unit="g/m³",
    )


# Silence unused-import warning — TriggerStateDescription is part of the
# public test surface used by these helpers but not directly referenced.
_ = TriggerStateDescription
