"""Test humidity conditions."""

from typing import Any

from tryke import Depends, fixture, test

from homeassistant.components.climate import (
    ATTR_CURRENT_HUMIDITY as CLIMATE_ATTR_CURRENT_HUMIDITY,
    HVACMode,
)
from homeassistant.components.humidifier import (
    ATTR_CURRENT_HUMIDITY as HUMIDIFIER_ATTR_CURRENT_HUMIDITY,
)
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
    ConditionStateDescription,
    assert_condition_behavior_all,
    assert_condition_behavior_any,
    assert_condition_gated_by_labs_flag,
    assert_condition_options_supported,
    parametrize_numerical_attribute_condition_above_below_all,
    parametrize_numerical_attribute_condition_above_below_any,
    parametrize_numerical_condition_above_below_all,
    parametrize_numerical_condition_above_below_any,
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


_HUMIDITY_UNIT_ATTRS = {ATTR_UNIT_OF_MEASUREMENT: "%"}


@test.cases(
    test.case("is_value", condition="humidity.is_value"),
)
async def humidity_conditions_gated_by_labs_flag(
    condition: str,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the humidity conditions are gated by the labs flag."""
    await assert_condition_gated_by_labs_flag(hass, caplog, condition)


_PLAIN_THRESHOLD = {"threshold": {"type": "above", "value": {"number": 50}}}


@test.cases(
    test.case(
        "is_value",
        condition_key="humidity.is_value",
        base_options=_PLAIN_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
)
async def humidity_condition_options_validation(
    condition_key: str,
    base_options: dict[str, Any] | None,
    supports_behavior: bool,
    supports_duration: bool,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that humidity conditions support the expected options."""
    await assert_condition_options_supported(
        hass,
        condition_key,
        base_options,
        supports_behavior=supports_behavior,
        supports_duration=supports_duration,
    )


_SENSOR_TARGET_PARAMS = parametrize_target_entities("sensor")
_CLIMATE_TARGET_PARAMS = parametrize_target_entities("climate")
_HUMIDIFIER_TARGET_PARAMS = parametrize_target_entities("humidifier")
_WEATHER_TARGET_PARAMS = parametrize_target_entities("weather")

_SENSOR_ANY_PARAMS = parametrize_numerical_condition_above_below_any(
    "humidity.is_value",
    device_class="humidity",
    unit_attributes=_HUMIDITY_UNIT_ATTRS,
)
_SENSOR_ALL_PARAMS = parametrize_numerical_condition_above_below_all(
    "humidity.is_value",
    device_class="humidity",
    unit_attributes=_HUMIDITY_UNIT_ATTRS,
)

_CLIMATE_ANY_PARAMS = parametrize_numerical_attribute_condition_above_below_any(
    "humidity.is_value",
    HVACMode.AUTO,
    CLIMATE_ATTR_CURRENT_HUMIDITY,
    attribute_required=True,
)
_CLIMATE_ALL_PARAMS = parametrize_numerical_attribute_condition_above_below_all(
    "humidity.is_value",
    HVACMode.AUTO,
    CLIMATE_ATTR_CURRENT_HUMIDITY,
    attribute_required=True,
)

_HUMIDIFIER_ANY_PARAMS = parametrize_numerical_attribute_condition_above_below_any(
    "humidity.is_value",
    STATE_ON,
    HUMIDIFIER_ATTR_CURRENT_HUMIDITY,
    attribute_required=True,
)
_HUMIDIFIER_ALL_PARAMS = parametrize_numerical_attribute_condition_above_below_all(
    "humidity.is_value",
    STATE_ON,
    HUMIDIFIER_ATTR_CURRENT_HUMIDITY,
    attribute_required=True,
)

_WEATHER_ANY_PARAMS = parametrize_numerical_attribute_condition_above_below_any(
    "humidity.is_value",
    "sunny",
    ATTR_WEATHER_HUMIDITY,
    attribute_required=True,
)
_WEATHER_ALL_PARAMS = parametrize_numerical_attribute_condition_above_below_all(
    "humidity.is_value",
    "sunny",
    ATTR_WEATHER_HUMIDITY,
    attribute_required=True,
)


@test
async def humidity_sensor_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_sensors: dict[str, list[str]] = Depends(target_sensors_fixture),
) -> None:
    """Test the humidity sensor condition with 'any' behavior."""
    for condition_target_config, entity_id, entities_in_target in _SENSOR_TARGET_PARAMS:
        for condition, condition_options, states in _SENSOR_ANY_PARAMS:
            await assert_condition_behavior_any(
                hass,
                target_entities=target_sensors,
                condition_target_config=condition_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                condition=condition,
                condition_options=condition_options,
                states=states,
            )


@test
async def humidity_sensor_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_sensors: dict[str, list[str]] = Depends(target_sensors_fixture),
) -> None:
    """Test the humidity sensor condition with 'all' behavior."""
    for condition_target_config, entity_id, entities_in_target in _SENSOR_TARGET_PARAMS:
        for condition, condition_options, states in _SENSOR_ALL_PARAMS:
            await assert_condition_behavior_all(
                hass,
                target_entities=target_sensors,
                condition_target_config=condition_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                condition=condition,
                condition_options=condition_options,
                states=states,
            )


@test
async def humidity_climate_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test the humidity climate condition with 'any' behavior."""
    for condition_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for condition, condition_options, states in _CLIMATE_ANY_PARAMS:
            await assert_condition_behavior_any(
                hass,
                target_entities=target_climates,
                condition_target_config=condition_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                condition=condition,
                condition_options=condition_options,
                states=states,
            )


@test
async def humidity_climate_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test the humidity climate condition with 'all' behavior."""
    for condition_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for condition, condition_options, states in _CLIMATE_ALL_PARAMS:
            await assert_condition_behavior_all(
                hass,
                target_entities=target_climates,
                condition_target_config=condition_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                condition=condition,
                condition_options=condition_options,
                states=states,
            )


@test
async def humidity_humidifier_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test the humidity humidifier condition with 'any' behavior."""
    for condition_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for condition, condition_options, states in _HUMIDIFIER_ANY_PARAMS:
            await assert_condition_behavior_any(
                hass,
                target_entities=target_humidifiers,
                condition_target_config=condition_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                condition=condition,
                condition_options=condition_options,
                states=states,
            )


@test
async def humidity_humidifier_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test the humidity humidifier condition with 'all' behavior."""
    for condition_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for condition, condition_options, states in _HUMIDIFIER_ALL_PARAMS:
            await assert_condition_behavior_all(
                hass,
                target_entities=target_humidifiers,
                condition_target_config=condition_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                condition=condition,
                condition_options=condition_options,
                states=states,
            )


@test
async def humidity_weather_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_weathers: dict[str, list[str]] = Depends(target_weathers_fixture),
) -> None:
    """Test the humidity weather condition with 'any' behavior."""
    for condition_target_config, entity_id, entities_in_target in _WEATHER_TARGET_PARAMS:
        for condition, condition_options, states in _WEATHER_ANY_PARAMS:
            await assert_condition_behavior_any(
                hass,
                target_entities=target_weathers,
                condition_target_config=condition_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                condition=condition,
                condition_options=condition_options,
                states=states,
            )


@test
async def humidity_weather_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_weathers: dict[str, list[str]] = Depends(target_weathers_fixture),
) -> None:
    """Test the humidity weather condition with 'all' behavior."""
    for condition_target_config, entity_id, entities_in_target in _WEATHER_TARGET_PARAMS:
        for condition, condition_options, states in _WEATHER_ALL_PARAMS:
            await assert_condition_behavior_all(
                hass,
                target_entities=target_weathers,
                condition_target_config=condition_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                condition=condition,
                condition_options=condition_options,
                states=states,
            )


# Silence unused-import warning — ConditionStateDescription is part of the
# public test surface used by these helpers but not directly referenced.
_ = ConditionStateDescription
