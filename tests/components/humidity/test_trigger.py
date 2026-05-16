"""Test humidity trigger."""

from typing import Any

from tryke import Depends, fixture, test

from homeassistant.components.climate import (
    ATTR_CURRENT_HUMIDITY as CLIMATE_ATTR_CURRENT_HUMIDITY,
    HVACMode,
)
from homeassistant.components.humidifier import (
    ATTR_CURRENT_HUMIDITY as HUMIDIFIER_ATTR_CURRENT_HUMIDITY,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.weather import ATTR_WEATHER_HUMIDITY
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, STATE_ON
from homeassistant.core import HomeAssistant

from ._fixtures import (
    enable_labs_preview_features,
    target_climates as target_climates_fixture,
    target_humidifiers as target_humidifiers_fixture,
    target_sensors as target_sensors_fixture,
    target_weathers as target_weathers_fixture,
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
    parametrize_numerical_state_value_changed_trigger_states,
    parametrize_numerical_state_value_crossed_threshold_trigger_states,
    parametrize_target_entities,
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
    test.case("changed", trigger_key="humidity.changed"),
    test.case("crossed_threshold", trigger_key="humidity.crossed_threshold"),
)
async def humidity_triggers_gated_by_labs_flag(
    trigger_key: str,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the humidity triggers are gated by the labs flag."""
    await assert_trigger_gated_by_labs_flag(hass, caplog, trigger_key)


_CHANGED_THRESHOLD = {"threshold": {"type": "any"}}

_PERCENT_CROSSED_THRESHOLD = {
    "threshold": {
        "type": "above",
        "value": {"number": 50, "unit_of_measurement": "%"},
    }
}


@test.cases(
    test.case(
        "changed",
        trigger_key="humidity.changed",
        base_options=_CHANGED_THRESHOLD,
        supports_behavior=False,
        supports_duration=False,
    ),
    test.case(
        "crossed_threshold",
        trigger_key="humidity.crossed_threshold",
        base_options=_PERCENT_CROSSED_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
)
async def humidity_trigger_options_validation(
    trigger_key: str,
    base_options: dict[str, Any] | None,
    supports_behavior: bool,
    supports_duration: bool,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that humidity triggers support the expected options."""
    await assert_trigger_options_supported(
        hass,
        trigger_key,
        base_options,
        supports_behavior=supports_behavior,
        supports_duration=supports_duration,
    )


# --- Sensor domain tests (value in state.state) ---


_SENSOR_TARGET_PARAMS = parametrize_target_entities("sensor")
_CLIMATE_TARGET_PARAMS = parametrize_target_entities("climate")
_HUMIDIFIER_TARGET_PARAMS = parametrize_target_entities("humidifier")
_WEATHER_TARGET_PARAMS = parametrize_target_entities("weather")

_SENSOR_BEHAVIOR_ANY_STATES = [
    *parametrize_numerical_state_value_changed_trigger_states(
        "humidity.changed",
        device_class=SensorDeviceClass.HUMIDITY,
        unit_attributes={ATTR_UNIT_OF_MEASUREMENT: "%"},
    ),
    *parametrize_numerical_state_value_crossed_threshold_trigger_states(
        "humidity.crossed_threshold",
        device_class=SensorDeviceClass.HUMIDITY,
        unit_attributes={ATTR_UNIT_OF_MEASUREMENT: "%"},
    ),
]

_SENSOR_CROSSED_STATES = [
    *parametrize_numerical_state_value_crossed_threshold_trigger_states(
        "humidity.crossed_threshold",
        device_class=SensorDeviceClass.HUMIDITY,
        unit_attributes={ATTR_UNIT_OF_MEASUREMENT: "%"},
    ),
]

_CLIMATE_BEHAVIOR_ANY_STATES = [
    *parametrize_numerical_attribute_changed_trigger_states(
        "humidity.changed",
        HVACMode.AUTO,
        CLIMATE_ATTR_CURRENT_HUMIDITY,
        attribute_required=True,
    ),
    *parametrize_numerical_attribute_crossed_threshold_trigger_states(
        "humidity.crossed_threshold",
        HVACMode.AUTO,
        CLIMATE_ATTR_CURRENT_HUMIDITY,
        attribute_required=True,
    ),
]

_CLIMATE_CROSSED_STATES = [
    *parametrize_numerical_attribute_crossed_threshold_trigger_states(
        "humidity.crossed_threshold",
        HVACMode.AUTO,
        CLIMATE_ATTR_CURRENT_HUMIDITY,
        attribute_required=True,
    ),
]

_HUMIDIFIER_BEHAVIOR_ANY_STATES = [
    *parametrize_numerical_attribute_changed_trigger_states(
        "humidity.changed",
        STATE_ON,
        HUMIDIFIER_ATTR_CURRENT_HUMIDITY,
        attribute_required=True,
    ),
    *parametrize_numerical_attribute_crossed_threshold_trigger_states(
        "humidity.crossed_threshold",
        STATE_ON,
        HUMIDIFIER_ATTR_CURRENT_HUMIDITY,
        attribute_required=True,
    ),
]

_HUMIDIFIER_CROSSED_STATES = [
    *parametrize_numerical_attribute_crossed_threshold_trigger_states(
        "humidity.crossed_threshold",
        STATE_ON,
        HUMIDIFIER_ATTR_CURRENT_HUMIDITY,
        attribute_required=True,
    ),
]

_WEATHER_BEHAVIOR_ANY_STATES = [
    *parametrize_numerical_attribute_changed_trigger_states(
        "humidity.changed",
        "sunny",
        ATTR_WEATHER_HUMIDITY,
        attribute_required=True,
    ),
    *parametrize_numerical_attribute_crossed_threshold_trigger_states(
        "humidity.crossed_threshold",
        "sunny",
        ATTR_WEATHER_HUMIDITY,
        attribute_required=True,
    ),
]

_WEATHER_CROSSED_STATES = [
    *parametrize_numerical_attribute_crossed_threshold_trigger_states(
        "humidity.crossed_threshold",
        "sunny",
        ATTR_WEATHER_HUMIDITY,
        attribute_required=True,
    ),
]


@test
async def humidity_trigger_sensor_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_sensors: dict[str, list[str]] = Depends(target_sensors_fixture),
) -> None:
    """Test humidity trigger fires for sensor entities with device_class humidity."""
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
async def humidity_trigger_sensor_crossed_threshold_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_sensors: dict[str, list[str]] = Depends(target_sensors_fixture),
) -> None:
    """Test humidity crossed_threshold trigger fires on the first sensor state change."""
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
async def humidity_trigger_sensor_crossed_threshold_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_sensors: dict[str, list[str]] = Depends(target_sensors_fixture),
) -> None:
    """Test humidity crossed_threshold trigger fires when the last sensor changes state."""
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


# --- Climate domain tests (value in current_humidity attribute) ---


@test
async def humidity_trigger_climate_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test humidity trigger fires for climate entities."""
    for trigger_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for trigger, trigger_options, states in _CLIMATE_BEHAVIOR_ANY_STATES:
            await assert_trigger_behavior_any(
                hass,
                target_entities=target_climates,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def humidity_trigger_climate_crossed_threshold_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test humidity crossed_threshold trigger fires on the first climate state change."""
    for trigger_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for trigger, trigger_options, states in _CLIMATE_CROSSED_STATES:
            await assert_trigger_behavior_first(
                hass,
                target_entities=target_climates,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def humidity_trigger_climate_crossed_threshold_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test humidity crossed_threshold trigger fires when the last climate changes state."""
    for trigger_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for trigger, trigger_options, states in _CLIMATE_CROSSED_STATES:
            await assert_trigger_behavior_last(
                hass,
                target_entities=target_climates,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


# --- Humidifier domain tests (value in current_humidity attribute) ---


@test
async def humidity_trigger_humidifier_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test humidity trigger fires for humidifier entities."""
    for trigger_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for trigger, trigger_options, states in _HUMIDIFIER_BEHAVIOR_ANY_STATES:
            await assert_trigger_behavior_any(
                hass,
                target_entities=target_humidifiers,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def humidity_trigger_humidifier_crossed_threshold_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test humidity crossed_threshold trigger fires on the first humidifier state change."""
    for trigger_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for trigger, trigger_options, states in _HUMIDIFIER_CROSSED_STATES:
            await assert_trigger_behavior_first(
                hass,
                target_entities=target_humidifiers,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def humidity_trigger_humidifier_crossed_threshold_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test humidity crossed_threshold trigger fires when the last humidifier changes state."""
    for trigger_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for trigger, trigger_options, states in _HUMIDIFIER_CROSSED_STATES:
            await assert_trigger_behavior_last(
                hass,
                target_entities=target_humidifiers,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


# --- Weather domain tests (value in humidity attribute) ---


@test
async def humidity_trigger_weather_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_weathers: dict[str, list[str]] = Depends(target_weathers_fixture),
) -> None:
    """Test humidity trigger fires for weather entities."""
    for trigger_target_config, entity_id, entities_in_target in _WEATHER_TARGET_PARAMS:
        for trigger, trigger_options, states in _WEATHER_BEHAVIOR_ANY_STATES:
            await assert_trigger_behavior_any(
                hass,
                target_entities=target_weathers,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def humidity_trigger_weather_crossed_threshold_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_weathers: dict[str, list[str]] = Depends(target_weathers_fixture),
) -> None:
    """Test humidity crossed_threshold trigger fires on the first weather state change."""
    for trigger_target_config, entity_id, entities_in_target in _WEATHER_TARGET_PARAMS:
        for trigger, trigger_options, states in _WEATHER_CROSSED_STATES:
            await assert_trigger_behavior_first(
                hass,
                target_entities=target_weathers,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def humidity_trigger_weather_crossed_threshold_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_weathers: dict[str, list[str]] = Depends(target_weathers_fixture),
) -> None:
    """Test humidity crossed_threshold trigger fires when the last weather changes state."""
    for trigger_target_config, entity_id, entities_in_target in _WEATHER_TARGET_PARAMS:
        for trigger, trigger_options, states in _WEATHER_CROSSED_STATES:
            await assert_trigger_behavior_last(
                hass,
                target_entities=target_weathers,
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
        trigger="humidity.changed",
        trigger_options={
            "threshold": {
                "type": "between",
                "value_min": {"entity": "sensor.humidity_above"},
                "value_max": {"entity": "sensor.humidity_below"},
            },
        },
        limit_entities=["sensor.humidity_above", "sensor.humidity_below"],
    ),
    test.case(
        "crossed_threshold",
        trigger="humidity.crossed_threshold",
        trigger_options={
            "threshold": {
                "type": "between",
                "value_min": {"entity": "sensor.humidity_lower"},
                "value_max": {"entity": "sensor.humidity_upper"},
            },
        },
        limit_entities=["sensor.humidity_lower", "sensor.humidity_upper"],
    ),
)
async def humidity_trigger_ignores_limit_entity_with_wrong_unit(
    trigger: str,
    trigger_options: dict[str, Any],
    limit_entities: list[str],
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test humidity triggers do not fire if limit entity unit is not %."""
    await assert_trigger_ignores_limit_entities_with_wrong_unit(
        hass,
        trigger=trigger,
        trigger_options=trigger_options,
        entity_id="climate.test_climate",
        reset_state={
            "state": HVACMode.AUTO,
            "attributes": {CLIMATE_ATTR_CURRENT_HUMIDITY: 0},
        },
        trigger_state={
            "state": HVACMode.AUTO,
            "attributes": {CLIMATE_ATTR_CURRENT_HUMIDITY: 50},
        },
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
