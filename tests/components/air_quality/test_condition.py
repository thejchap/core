"""Test air quality conditions."""

from typing import Any

from tryke import Depends, fixture, test

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_BILLION,
    CONCENTRATION_PARTS_PER_MILLION,
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
    ConditionStateDescription,
    assert_condition_behavior_all,
    assert_condition_behavior_any,
    assert_condition_gated_by_labs_flag,
    assert_condition_options_supported,
    assert_numerical_condition_unit_conversion,
    parametrize_condition_states_all,
    parametrize_condition_states_any,
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


_UGM3_UNIT_ATTRIBUTES = {
    ATTR_UNIT_OF_MEASUREMENT: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
}
_PPB_UNIT_ATTRIBUTES = {ATTR_UNIT_OF_MEASUREMENT: CONCENTRATION_PARTS_PER_BILLION}
_PPM_UNIT_ATTRIBUTES = {ATTR_UNIT_OF_MEASUREMENT: CONCENTRATION_PARTS_PER_MILLION}


@test.cases(
    test.case("is_gas_detected", condition="air_quality.is_gas_detected"),
    test.case("is_gas_cleared", condition="air_quality.is_gas_cleared"),
    test.case("is_co_detected", condition="air_quality.is_co_detected"),
    test.case("is_co_cleared", condition="air_quality.is_co_cleared"),
    test.case("is_smoke_detected", condition="air_quality.is_smoke_detected"),
    test.case("is_smoke_cleared", condition="air_quality.is_smoke_cleared"),
    test.case("is_co_value", condition="air_quality.is_co_value"),
    test.case("is_co2_value", condition="air_quality.is_co2_value"),
    test.case("is_pm1_value", condition="air_quality.is_pm1_value"),
    test.case("is_pm25_value", condition="air_quality.is_pm25_value"),
    test.case("is_pm4_value", condition="air_quality.is_pm4_value"),
    test.case("is_pm10_value", condition="air_quality.is_pm10_value"),
    test.case("is_ozone_value", condition="air_quality.is_ozone_value"),
    test.case("is_voc_value", condition="air_quality.is_voc_value"),
    test.case("is_voc_ratio_value", condition="air_quality.is_voc_ratio_value"),
    test.case("is_no_value", condition="air_quality.is_no_value"),
    test.case("is_no2_value", condition="air_quality.is_no2_value"),
    test.case("is_n2o_value", condition="air_quality.is_n2o_value"),
    test.case("is_so2_value", condition="air_quality.is_so2_value"),
)
async def air_quality_conditions_gated_by_labs_flag(
    condition: str,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the air quality conditions are gated by the labs flag."""
    await assert_condition_gated_by_labs_flag(hass, caplog, condition)


_PLAIN_THRESHOLD = {"threshold": {"type": "above", "value": {"number": 50}}}
_PPB_THRESHOLD = {
    "threshold": {
        "type": "above",
        "value": {
            "number": 50,
            "unit_of_measurement": CONCENTRATION_PARTS_PER_BILLION,
        },
    }
}
_UGM3_THRESHOLD = {
    "threshold": {
        "type": "above",
        "value": {
            "number": 50,
            "unit_of_measurement": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        },
    }
}


@test.cases(
    test.case(
        "is_gas_detected",
        condition_key="air_quality.is_gas_detected",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_gas_cleared",
        condition_key="air_quality.is_gas_cleared",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_co_detected",
        condition_key="air_quality.is_co_detected",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_co_cleared",
        condition_key="air_quality.is_co_cleared",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_smoke_detected",
        condition_key="air_quality.is_smoke_detected",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_smoke_cleared",
        condition_key="air_quality.is_smoke_cleared",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_co_value",
        condition_key="air_quality.is_co_value",
        base_options=_UGM3_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_ozone_value",
        condition_key="air_quality.is_ozone_value",
        base_options=_UGM3_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_voc_value",
        condition_key="air_quality.is_voc_value",
        base_options=_UGM3_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_no_value",
        condition_key="air_quality.is_no_value",
        base_options=_UGM3_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_no2_value",
        condition_key="air_quality.is_no2_value",
        base_options=_UGM3_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_so2_value",
        condition_key="air_quality.is_so2_value",
        base_options=_UGM3_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_voc_ratio_value",
        condition_key="air_quality.is_voc_ratio_value",
        base_options=_PPB_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_co2_value",
        condition_key="air_quality.is_co2_value",
        base_options=_PLAIN_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_pm1_value",
        condition_key="air_quality.is_pm1_value",
        base_options=_PLAIN_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_pm25_value",
        condition_key="air_quality.is_pm25_value",
        base_options=_PLAIN_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_pm4_value",
        condition_key="air_quality.is_pm4_value",
        base_options=_PLAIN_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_pm10_value",
        condition_key="air_quality.is_pm10_value",
        base_options=_PLAIN_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_n2o_value",
        condition_key="air_quality.is_n2o_value",
        base_options=_PLAIN_THRESHOLD,
        supports_behavior=True,
        supports_duration=True,
    ),
)
async def air_quality_condition_options_validation(
    condition_key: str,
    base_options: dict[str, Any] | None,
    supports_behavior: bool,
    supports_duration: bool,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that air_quality conditions support the expected options."""
    await assert_condition_options_supported(
        hass,
        condition_key,
        base_options,
        supports_behavior=supports_behavior,
        supports_duration=supports_duration,
    )


_BINARY_SENSOR_TARGET_PARAMS = parametrize_target_entities("binary_sensor")
_SENSOR_TARGET_PARAMS = parametrize_target_entities("sensor")

_BINARY_ANY_PARAMS = [
    *parametrize_condition_states_any(
        condition="air_quality.is_gas_detected",
        target_states=[STATE_ON],
        other_states=[STATE_OFF],
        required_filter_attributes={ATTR_DEVICE_CLASS: BinarySensorDeviceClass.GAS},
    ),
    *parametrize_condition_states_any(
        condition="air_quality.is_gas_cleared",
        target_states=[STATE_OFF],
        other_states=[STATE_ON],
        required_filter_attributes={ATTR_DEVICE_CLASS: BinarySensorDeviceClass.GAS},
    ),
    *parametrize_condition_states_any(
        condition="air_quality.is_co_detected",
        target_states=[STATE_ON],
        other_states=[STATE_OFF],
        required_filter_attributes={ATTR_DEVICE_CLASS: BinarySensorDeviceClass.CO},
    ),
    *parametrize_condition_states_any(
        condition="air_quality.is_co_cleared",
        target_states=[STATE_OFF],
        other_states=[STATE_ON],
        required_filter_attributes={ATTR_DEVICE_CLASS: BinarySensorDeviceClass.CO},
    ),
    *parametrize_condition_states_any(
        condition="air_quality.is_smoke_detected",
        target_states=[STATE_ON],
        other_states=[STATE_OFF],
        required_filter_attributes={ATTR_DEVICE_CLASS: BinarySensorDeviceClass.SMOKE},
    ),
    *parametrize_condition_states_any(
        condition="air_quality.is_smoke_cleared",
        target_states=[STATE_OFF],
        other_states=[STATE_ON],
        required_filter_attributes={ATTR_DEVICE_CLASS: BinarySensorDeviceClass.SMOKE},
    ),
]

_BINARY_ALL_PARAMS = [
    *parametrize_condition_states_all(
        condition="air_quality.is_gas_detected",
        target_states=[STATE_ON],
        other_states=[STATE_OFF],
        required_filter_attributes={ATTR_DEVICE_CLASS: BinarySensorDeviceClass.GAS},
    ),
    *parametrize_condition_states_all(
        condition="air_quality.is_gas_cleared",
        target_states=[STATE_OFF],
        other_states=[STATE_ON],
        required_filter_attributes={ATTR_DEVICE_CLASS: BinarySensorDeviceClass.GAS},
    ),
    *parametrize_condition_states_all(
        condition="air_quality.is_co_detected",
        target_states=[STATE_ON],
        other_states=[STATE_OFF],
        required_filter_attributes={ATTR_DEVICE_CLASS: BinarySensorDeviceClass.CO},
    ),
    *parametrize_condition_states_all(
        condition="air_quality.is_co_cleared",
        target_states=[STATE_OFF],
        other_states=[STATE_ON],
        required_filter_attributes={ATTR_DEVICE_CLASS: BinarySensorDeviceClass.CO},
    ),
    *parametrize_condition_states_all(
        condition="air_quality.is_smoke_detected",
        target_states=[STATE_ON],
        other_states=[STATE_OFF],
        required_filter_attributes={ATTR_DEVICE_CLASS: BinarySensorDeviceClass.SMOKE},
    ),
    *parametrize_condition_states_all(
        condition="air_quality.is_smoke_cleared",
        target_states=[STATE_OFF],
        other_states=[STATE_ON],
        required_filter_attributes={ATTR_DEVICE_CLASS: BinarySensorDeviceClass.SMOKE},
    ),
]

_NUMERICAL_WITH_UNIT_ANY_PARAMS = [
    *parametrize_numerical_condition_above_below_any(
        "air_quality.is_co_value",
        device_class="carbon_monoxide",
        threshold_unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_any(
        "air_quality.is_ozone_value",
        device_class="ozone",
        threshold_unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_any(
        "air_quality.is_voc_value",
        device_class="volatile_organic_compounds",
        threshold_unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_any(
        "air_quality.is_voc_ratio_value",
        device_class="volatile_organic_compounds_parts",
        threshold_unit=CONCENTRATION_PARTS_PER_BILLION,
        unit_attributes=_PPB_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_any(
        "air_quality.is_no_value",
        device_class="nitrogen_monoxide",
        threshold_unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_any(
        "air_quality.is_no2_value",
        device_class="nitrogen_dioxide",
        threshold_unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_any(
        "air_quality.is_so2_value",
        device_class="sulphur_dioxide",
        threshold_unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
]

_NUMERICAL_WITH_UNIT_ALL_PARAMS = [
    *parametrize_numerical_condition_above_below_all(
        "air_quality.is_co_value",
        device_class="carbon_monoxide",
        threshold_unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_all(
        "air_quality.is_ozone_value",
        device_class="ozone",
        threshold_unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_all(
        "air_quality.is_voc_value",
        device_class="volatile_organic_compounds",
        threshold_unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_all(
        "air_quality.is_voc_ratio_value",
        device_class="volatile_organic_compounds_parts",
        threshold_unit=CONCENTRATION_PARTS_PER_BILLION,
        unit_attributes=_PPB_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_all(
        "air_quality.is_no_value",
        device_class="nitrogen_monoxide",
        threshold_unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_all(
        "air_quality.is_no2_value",
        device_class="nitrogen_dioxide",
        threshold_unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_all(
        "air_quality.is_so2_value",
        device_class="sulphur_dioxide",
        threshold_unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
]

_NUMERICAL_NO_UNIT_ANY_PARAMS = [
    *parametrize_numerical_condition_above_below_any(
        "air_quality.is_co2_value",
        device_class="carbon_dioxide",
        unit_attributes=_PPM_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_any(
        "air_quality.is_pm1_value",
        device_class="pm1",
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_any(
        "air_quality.is_pm25_value",
        device_class="pm25",
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_any(
        "air_quality.is_pm4_value",
        device_class="pm4",
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_any(
        "air_quality.is_pm10_value",
        device_class="pm10",
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_any(
        "air_quality.is_n2o_value",
        device_class="nitrous_oxide",
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
]

_NUMERICAL_NO_UNIT_ALL_PARAMS = [
    *parametrize_numerical_condition_above_below_all(
        "air_quality.is_co2_value",
        device_class="carbon_dioxide",
        unit_attributes=_PPM_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_all(
        "air_quality.is_pm1_value",
        device_class="pm1",
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_all(
        "air_quality.is_pm25_value",
        device_class="pm25",
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_all(
        "air_quality.is_pm4_value",
        device_class="pm4",
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_all(
        "air_quality.is_pm10_value",
        device_class="pm10",
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
    *parametrize_numerical_condition_above_below_all(
        "air_quality.is_n2o_value",
        device_class="nitrous_oxide",
        unit_attributes=_UGM3_UNIT_ATTRIBUTES,
    ),
]


@test
async def air_quality_binary_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_binary_sensors: dict[str, list[str]] = Depends(target_binary_sensors_fixture),
) -> None:
    """Test the air quality binary sensor condition with 'any' behavior."""
    for (
        condition_target_config,
        entity_id,
        entities_in_target,
    ) in _BINARY_SENSOR_TARGET_PARAMS:
        for condition, condition_options, states in _BINARY_ANY_PARAMS:
            await assert_condition_behavior_any(
                hass,
                target_entities=target_binary_sensors,
                condition_target_config=condition_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                condition=condition,
                condition_options=condition_options,
                states=states,
            )


@test
async def air_quality_binary_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_binary_sensors: dict[str, list[str]] = Depends(target_binary_sensors_fixture),
) -> None:
    """Test the air quality binary sensor condition with 'all' behavior."""
    for (
        condition_target_config,
        entity_id,
        entities_in_target,
    ) in _BINARY_SENSOR_TARGET_PARAMS:
        for condition, condition_options, states in _BINARY_ALL_PARAMS:
            await assert_condition_behavior_all(
                hass,
                target_entities=target_binary_sensors,
                condition_target_config=condition_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                condition=condition,
                condition_options=condition_options,
                states=states,
            )


@test
async def air_quality_numerical_with_unit_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_sensors: dict[str, list[str]] = Depends(target_sensors_fixture),
) -> None:
    """Test air quality numerical conditions with unit conversion and 'any' behavior."""
    for condition_target_config, entity_id, entities_in_target in _SENSOR_TARGET_PARAMS:
        for condition, condition_options, states in _NUMERICAL_WITH_UNIT_ANY_PARAMS:
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
async def air_quality_numerical_with_unit_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_sensors: dict[str, list[str]] = Depends(target_sensors_fixture),
) -> None:
    """Test air quality numerical conditions with unit conversion and 'all' behavior."""
    for condition_target_config, entity_id, entities_in_target in _SENSOR_TARGET_PARAMS:
        for condition, condition_options, states in _NUMERICAL_WITH_UNIT_ALL_PARAMS:
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
async def air_quality_numerical_no_unit_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_sensors: dict[str, list[str]] = Depends(target_sensors_fixture),
) -> None:
    """Test air quality numerical conditions without unit conversion and 'any' behavior."""
    for condition_target_config, entity_id, entities_in_target in _SENSOR_TARGET_PARAMS:
        for condition, condition_options, states in _NUMERICAL_NO_UNIT_ANY_PARAMS:
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
async def air_quality_numerical_no_unit_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_sensors: dict[str, list[str]] = Depends(target_sensors_fixture),
) -> None:
    """Test air quality numerical conditions without unit conversion and 'all' behavior."""
    for condition_target_config, entity_id, entities_in_target in _SENSOR_TARGET_PARAMS:
        for condition, condition_options, states in _NUMERICAL_NO_UNIT_ALL_PARAMS:
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
async def air_quality_condition_unit_conversion_co(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that the CO condition converts units correctly."""
    _unit_ugm3 = {ATTR_UNIT_OF_MEASUREMENT: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER}
    _unit_ppm = {ATTR_UNIT_OF_MEASUREMENT: CONCENTRATION_PARTS_PER_MILLION}
    _unit_invalid = {ATTR_UNIT_OF_MEASUREMENT: "not_a_valid_unit"}

    await assert_numerical_condition_unit_conversion(
        hass,
        condition="air_quality.is_co_value",
        entity_id="sensor.test",
        pass_states=[
            {
                "state": "500",
                "attributes": {
                    "device_class": "carbon_monoxide",
                    ATTR_UNIT_OF_MEASUREMENT: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                },
            }
        ],
        fail_states=[
            {
                "state": "100",
                "attributes": {
                    "device_class": "carbon_monoxide",
                    ATTR_UNIT_OF_MEASUREMENT: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                },
            }
        ],
        numerical_condition_options=[
            {
                "threshold": {
                    "type": "between",
                    "value_min": {
                        "number": 0.2,
                        "unit_of_measurement": CONCENTRATION_PARTS_PER_MILLION,
                    },
                    "value_max": {
                        "number": 0.8,
                        "unit_of_measurement": CONCENTRATION_PARTS_PER_MILLION,
                    },
                }
            },
            {
                "threshold": {
                    "type": "between",
                    "value_min": {
                        "number": 200,
                        "unit_of_measurement": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                    },
                    "value_max": {
                        "number": 800,
                        "unit_of_measurement": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
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
                {"state": "0.2", "attributes": _unit_ppm},
                {"state": "0.8", "attributes": _unit_ppm},
            ),
            (
                {"state": "200", "attributes": _unit_ugm3},
                {"state": "800", "attributes": _unit_ugm3},
            ),
        ],
        invalid_limit_entity_states=[
            (
                {"state": "0.2", "attributes": _unit_invalid},
                {"state": "0.8", "attributes": _unit_invalid},
            ),
            (
                {"state": "200", "attributes": _unit_invalid},
                {"state": "800", "attributes": _unit_invalid},
            ),
        ],
    )


# Silence unused-import warning — ConditionStateDescription is part of the
# public test surface used by these helpers but not directly referenced.
_ = ConditionStateDescription
