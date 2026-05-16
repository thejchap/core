"""Test temperature conditions."""

from typing import Any

from tryke import Depends, fixture, test

from homeassistant.components.climate import HVACMode
from homeassistant.components.weather import ATTR_WEATHER_TEMPERATURE_UNIT
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, UnitOfTemperature
from homeassistant.core import HomeAssistant

from ._fixtures import (
    enable_labs_preview_features,
    target_climates as target_climates_fixture,
    target_sensors as target_sensors_fixture,
    target_water_heaters as target_water_heaters_fixture,
    target_weathers as target_weathers_fixture,
)

from tests.components.common import (
    ConditionStateDescription,
    assert_condition_behavior_all,
    assert_condition_behavior_any,
    assert_condition_gated_by_labs_flag,
    assert_condition_options_supported,
    assert_numerical_condition_unit_conversion,
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


_WEATHER_UNIT_ATTRIBUTES = {ATTR_WEATHER_TEMPERATURE_UNIT: UnitOfTemperature.CELSIUS}


@test.cases(
    test.case("is_value", condition="temperature.is_value"),
)
async def temperature_conditions_gated_by_labs_flag(
    condition: str,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the temperature conditions are gated by the labs flag."""
    await assert_condition_gated_by_labs_flag(hass, caplog, condition)


_CELSIUS_THRESHOLD = {
    "threshold": {
        "type": "above",
        "value": {"number": 20, "unit_of_measurement": "°C"},
    }
}


@test.cases(
    test.case(
        "is_value",
        condition_key="temperature.is_value",
        base_options=_CELSIUS_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
)
async def temperature_condition_options_validation(
    condition_key: str,
    base_options: dict[str, Any] | None,
    supports_behavior: bool,
    supports_duration: bool,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that temperature conditions support the expected options."""
    await assert_condition_options_supported(
        hass,
        condition_key,
        base_options,
        supports_behavior=supports_behavior,
        supports_duration=supports_duration,
    )


_SENSOR_TARGET_PARAMS = parametrize_target_entities("sensor")
_CLIMATE_TARGET_PARAMS = parametrize_target_entities("climate")
_WATER_HEATER_TARGET_PARAMS = parametrize_target_entities("water_heater")
_WEATHER_TARGET_PARAMS = parametrize_target_entities("weather")

_SENSOR_ANY_PARAMS = parametrize_numerical_condition_above_below_any(
    "temperature.is_value",
    device_class="temperature",
    threshold_unit=UnitOfTemperature.CELSIUS,
    unit_attributes={ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
)
_SENSOR_ALL_PARAMS = parametrize_numerical_condition_above_below_all(
    "temperature.is_value",
    device_class="temperature",
    threshold_unit=UnitOfTemperature.CELSIUS,
    unit_attributes={ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
)

_CLIMATE_ANY_PARAMS = parametrize_numerical_attribute_condition_above_below_any(
    "temperature.is_value",
    HVACMode.AUTO,
    "current_temperature",
    threshold_unit=UnitOfTemperature.CELSIUS,
    attribute_required=True,
)
_CLIMATE_ALL_PARAMS = parametrize_numerical_attribute_condition_above_below_all(
    "temperature.is_value",
    HVACMode.AUTO,
    "current_temperature",
    threshold_unit=UnitOfTemperature.CELSIUS,
    attribute_required=True,
)

_WATER_HEATER_ANY_PARAMS = parametrize_numerical_attribute_condition_above_below_any(
    "temperature.is_value",
    "eco",
    "current_temperature",
    threshold_unit=UnitOfTemperature.CELSIUS,
    attribute_required=True,
)
_WATER_HEATER_ALL_PARAMS = parametrize_numerical_attribute_condition_above_below_all(
    "temperature.is_value",
    "eco",
    "current_temperature",
    threshold_unit=UnitOfTemperature.CELSIUS,
    attribute_required=True,
)

_WEATHER_ANY_PARAMS = parametrize_numerical_attribute_condition_above_below_any(
    "temperature.is_value",
    "sunny",
    "temperature",
    threshold_unit=UnitOfTemperature.CELSIUS,
    unit_attributes=_WEATHER_UNIT_ATTRIBUTES,
    attribute_required=True,
)
_WEATHER_ALL_PARAMS = parametrize_numerical_attribute_condition_above_below_all(
    "temperature.is_value",
    "sunny",
    "temperature",
    threshold_unit=UnitOfTemperature.CELSIUS,
    unit_attributes=_WEATHER_UNIT_ATTRIBUTES,
    attribute_required=True,
)


@test
async def temperature_sensor_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_sensors: dict[str, list[str]] = Depends(target_sensors_fixture),
) -> None:
    """Test the temperature sensor condition with 'any' behavior."""
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
async def temperature_sensor_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_sensors: dict[str, list[str]] = Depends(target_sensors_fixture),
) -> None:
    """Test the temperature sensor condition with 'all' behavior."""
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
async def temperature_climate_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test the temperature climate condition with 'any' behavior."""
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
async def temperature_climate_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test the temperature climate condition with 'all' behavior."""
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
async def temperature_water_heater_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_water_heaters: dict[str, list[str]] = Depends(target_water_heaters_fixture),
) -> None:
    """Test the temperature water heater condition with 'any' behavior."""
    for (
        condition_target_config,
        entity_id,
        entities_in_target,
    ) in _WATER_HEATER_TARGET_PARAMS:
        for condition, condition_options, states in _WATER_HEATER_ANY_PARAMS:
            await assert_condition_behavior_any(
                hass,
                target_entities=target_water_heaters,
                condition_target_config=condition_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                condition=condition,
                condition_options=condition_options,
                states=states,
            )


@test
async def temperature_water_heater_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_water_heaters: dict[str, list[str]] = Depends(target_water_heaters_fixture),
) -> None:
    """Test the temperature water heater condition with 'all' behavior."""
    for (
        condition_target_config,
        entity_id,
        entities_in_target,
    ) in _WATER_HEATER_TARGET_PARAMS:
        for condition, condition_options, states in _WATER_HEATER_ALL_PARAMS:
            await assert_condition_behavior_all(
                hass,
                target_entities=target_water_heaters,
                condition_target_config=condition_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                condition=condition,
                condition_options=condition_options,
                states=states,
            )


@test
async def temperature_weather_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_weathers: dict[str, list[str]] = Depends(target_weathers_fixture),
) -> None:
    """Test the temperature weather condition with 'any' behavior."""
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
async def temperature_weather_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_weathers: dict[str, list[str]] = Depends(target_weathers_fixture),
) -> None:
    """Test the temperature weather condition with 'all' behavior."""
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


@test
async def temperature_condition_unit_conversion_sensor(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that the temperature condition converts units correctly for sensors."""
    _unit_celsius = {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    _unit_fahrenheit = {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT}
    _unit_invalid = {ATTR_UNIT_OF_MEASUREMENT: "not_a_valid_unit"}

    await assert_numerical_condition_unit_conversion(
        hass,
        condition="temperature.is_value",
        entity_id="sensor.test",
        pass_states=[
            {
                "state": "25",
                "attributes": {
                    "device_class": "temperature",
                    ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
                },
            }
        ],
        fail_states=[
            {
                "state": "20",
                "attributes": {
                    "device_class": "temperature",
                    ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
                },
            }
        ],
        numerical_condition_options=[
            {
                "threshold": {
                    "type": "between",
                    "value_min": {
                        "number": 75,
                        "unit_of_measurement": UnitOfTemperature.FAHRENHEIT,
                    },
                    "value_max": {
                        "number": 90,
                        "unit_of_measurement": UnitOfTemperature.FAHRENHEIT,
                    },
                }
            },
            {
                "threshold": {
                    "type": "between",
                    "value_min": {
                        "number": 24,
                        "unit_of_measurement": UnitOfTemperature.CELSIUS,
                    },
                    "value_max": {
                        "number": 30,
                        "unit_of_measurement": UnitOfTemperature.CELSIUS,
                    },
                }
            },
        ],
        limit_entity_condition_options={
            "threshold": {
                "type": "between",
                "value_min": {"entity": "sensor.above"},
                "value_max": {"entity": "sensor.below"},
            }
        },
        limit_entities=("sensor.above", "sensor.below"),
        limit_entity_states=[
            (
                {"state": "75", "attributes": _unit_fahrenheit},
                {"state": "90", "attributes": _unit_fahrenheit},
            ),
            (
                {"state": "24", "attributes": _unit_celsius},
                {"state": "30", "attributes": _unit_celsius},
            ),
        ],
        invalid_limit_entity_states=[
            (
                {"state": "75", "attributes": _unit_invalid},
                {"state": "90", "attributes": _unit_invalid},
            ),
            (
                {"state": "24", "attributes": _unit_invalid},
                {"state": "30", "attributes": _unit_invalid},
            ),
        ],
    )


@test
async def temperature_condition_unit_conversion_climate(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that the temperature condition converts units correctly for climate."""
    _unit_celsius = {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    _unit_fahrenheit = {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT}
    _unit_invalid = {ATTR_UNIT_OF_MEASUREMENT: "not_a_valid_unit"}

    await assert_numerical_condition_unit_conversion(
        hass,
        condition="temperature.is_value",
        entity_id="climate.test",
        pass_states=[
            {"state": HVACMode.AUTO, "attributes": {"current_temperature": 25}}
        ],
        fail_states=[
            {"state": HVACMode.AUTO, "attributes": {"current_temperature": 20}}
        ],
        numerical_condition_options=[
            {
                "threshold": {
                    "type": "between",
                    "value_min": {
                        "number": 75,
                        "unit_of_measurement": UnitOfTemperature.FAHRENHEIT,
                    },
                    "value_max": {
                        "number": 90,
                        "unit_of_measurement": UnitOfTemperature.FAHRENHEIT,
                    },
                }
            },
            {
                "threshold": {
                    "type": "between",
                    "value_min": {
                        "number": 24,
                        "unit_of_measurement": UnitOfTemperature.CELSIUS,
                    },
                    "value_max": {
                        "number": 30,
                        "unit_of_measurement": UnitOfTemperature.CELSIUS,
                    },
                }
            },
        ],
        limit_entity_condition_options={
            "threshold": {
                "type": "between",
                "value_min": {"entity": "sensor.above"},
                "value_max": {"entity": "sensor.below"},
            }
        },
        limit_entities=("sensor.above", "sensor.below"),
        limit_entity_states=[
            (
                {"state": "75", "attributes": _unit_fahrenheit},
                {"state": "90", "attributes": _unit_fahrenheit},
            ),
            (
                {"state": "24", "attributes": _unit_celsius},
                {"state": "30", "attributes": _unit_celsius},
            ),
        ],
        invalid_limit_entity_states=[
            (
                {"state": "75", "attributes": _unit_invalid},
                {"state": "90", "attributes": _unit_invalid},
            ),
            (
                {"state": "24", "attributes": _unit_invalid},
                {"state": "30", "attributes": _unit_invalid},
            ),
        ],
    )


# Silence unused-import warning — ConditionStateDescription is part of the
# public test surface used by these helpers but not directly referenced.
_ = ConditionStateDescription
