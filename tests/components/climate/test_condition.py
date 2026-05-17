"""Test climate conditions."""

from typing import Any

from tryke import Depends, fixture, test

from homeassistant.components.climate.const import (
    ATTR_HUMIDITY,
    ATTR_HVAC_ACTION,
    HVACAction,
    HVACMode,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    ATTR_UNIT_OF_MEASUREMENT,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant

from ._fixtures import (
    enable_labs_preview_features,
    target_climates as target_climates_fixture,
)

from tests.components.common import (
    ConditionStateDescription,
    assert_condition_behavior_all,
    assert_condition_behavior_any,
    assert_condition_gated_by_labs_flag,
    assert_condition_options_supported,
    assert_numerical_condition_unit_conversion,
    other_states,
    parametrize_condition_states_all,
    parametrize_condition_states_any,
    parametrize_numerical_attribute_condition_above_below_all,
    parametrize_numerical_attribute_condition_above_below_any,
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
    test.case("is_off", condition="climate.is_off"),
    test.case("is_on", condition="climate.is_on"),
    test.case("is_cooling", condition="climate.is_cooling"),
    test.case("is_drying", condition="climate.is_drying"),
    test.case("is_heating", condition="climate.is_heating"),
    test.case("is_hvac_mode", condition="climate.is_hvac_mode"),
    test.case("target_humidity", condition="climate.target_humidity"),
    test.case("target_temperature", condition="climate.target_temperature"),
)
async def climate_conditions_gated_by_labs_flag(
    condition: str,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the climate conditions are gated by the labs flag."""
    await assert_condition_gated_by_labs_flag(hass, caplog, condition)


@test.cases(
    test.case(
        "is_off",
        condition_key="climate.is_off",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_on",
        condition_key="climate.is_on",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_cooling",
        condition_key="climate.is_cooling",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_drying",
        condition_key="climate.is_drying",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_heating",
        condition_key="climate.is_heating",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
)
async def climate_condition_options_validation(
    condition_key: str,
    base_options: dict[str, Any] | None,
    supports_behavior: bool,
    supports_duration: bool,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that climate conditions support the expected options."""
    await assert_condition_options_supported(
        hass,
        condition_key,
        base_options,
        supports_behavior=supports_behavior,
        supports_duration=supports_duration,
    )


_CLIMATE_TARGET_PARAMS = parametrize_target_entities("climate")

_STATE_CONDITION_ANY_PARAMS = [
    *parametrize_condition_states_any(
        condition="climate.is_off",
        target_states=[HVACMode.OFF],
        other_states=other_states(HVACMode.OFF),
    ),
    *parametrize_condition_states_any(
        condition="climate.is_on",
        target_states=[
            HVACMode.AUTO,
            HVACMode.COOL,
            HVACMode.DRY,
            HVACMode.FAN_ONLY,
            HVACMode.HEAT,
            HVACMode.HEAT_COOL,
        ],
        other_states=[HVACMode.OFF],
    ),
    *(
        param
        for mode in HVACMode
        for param in parametrize_condition_states_any(
            condition="climate.is_hvac_mode",
            condition_options={"hvac_mode": [mode]},
            target_states=[mode],
            other_states=[m for m in HVACMode if m != mode],
        )
    ),
    *parametrize_condition_states_any(
        condition="climate.is_hvac_mode",
        condition_options={"hvac_mode": [HVACMode.HEAT, HVACMode.COOL]},
        target_states=[HVACMode.HEAT, HVACMode.COOL],
        other_states=[
            m for m in HVACMode if m not in (HVACMode.HEAT, HVACMode.COOL)
        ],
    ),
]

_STATE_CONDITION_ALL_PARAMS = [
    *parametrize_condition_states_all(
        condition="climate.is_off",
        target_states=[HVACMode.OFF],
        other_states=other_states(HVACMode.OFF),
    ),
    *parametrize_condition_states_all(
        condition="climate.is_on",
        target_states=[
            HVACMode.AUTO,
            HVACMode.COOL,
            HVACMode.DRY,
            HVACMode.FAN_ONLY,
            HVACMode.HEAT,
            HVACMode.HEAT_COOL,
        ],
        other_states=[HVACMode.OFF],
    ),
    *(
        param
        for mode in HVACMode
        for param in parametrize_condition_states_all(
            condition="climate.is_hvac_mode",
            condition_options={"hvac_mode": [mode]},
            target_states=[mode],
            other_states=[m for m in HVACMode if m != mode],
        )
    ),
    *parametrize_condition_states_all(
        condition="climate.is_hvac_mode",
        condition_options={"hvac_mode": [HVACMode.HEAT, HVACMode.COOL]},
        target_states=[HVACMode.HEAT, HVACMode.COOL],
        other_states=[
            m for m in HVACMode if m not in (HVACMode.HEAT, HVACMode.COOL)
        ],
    ),
]

_ATTRIBUTE_CONDITION_ANY_PARAMS = [
    *parametrize_condition_states_any(
        condition="climate.is_cooling",
        target_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.COOLING})],
        other_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.IDLE})],
    ),
    *parametrize_condition_states_any(
        condition="climate.is_drying",
        target_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.DRYING})],
        other_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.IDLE})],
    ),
    *parametrize_condition_states_any(
        condition="climate.is_heating",
        target_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.HEATING})],
        other_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.IDLE})],
    ),
]

_ATTRIBUTE_CONDITION_ALL_PARAMS = [
    *parametrize_condition_states_all(
        condition="climate.is_cooling",
        target_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.COOLING})],
        other_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.IDLE})],
    ),
    *parametrize_condition_states_all(
        condition="climate.is_drying",
        target_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.DRYING})],
        other_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.IDLE})],
    ),
    *parametrize_condition_states_all(
        condition="climate.is_heating",
        target_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.HEATING})],
        other_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.IDLE})],
    ),
]

_NUMERICAL_CONDITION_ANY_PARAMS = [
    *parametrize_numerical_attribute_condition_above_below_any(
        "climate.target_humidity",
        HVACMode.AUTO,
        ATTR_HUMIDITY,
        attribute_required=True,
    ),
    *parametrize_numerical_attribute_condition_above_below_any(
        "climate.target_temperature",
        HVACMode.AUTO,
        ATTR_TEMPERATURE,
        threshold_unit=UnitOfTemperature.CELSIUS,
        attribute_required=True,
    ),
]

_NUMERICAL_CONDITION_ALL_PARAMS = [
    *parametrize_numerical_attribute_condition_above_below_all(
        "climate.target_humidity",
        HVACMode.AUTO,
        ATTR_HUMIDITY,
        attribute_required=True,
    ),
    *parametrize_numerical_attribute_condition_above_below_all(
        "climate.target_temperature",
        HVACMode.AUTO,
        ATTR_TEMPERATURE,
        threshold_unit=UnitOfTemperature.CELSIUS,
        attribute_required=True,
    ),
]


@test
async def climate_state_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test the climate state condition with the 'any' behavior."""
    for condition_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for condition, condition_options, states in _STATE_CONDITION_ANY_PARAMS:
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
async def climate_state_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test the climate state condition with the 'all' behavior."""
    for condition_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for condition, condition_options, states in _STATE_CONDITION_ALL_PARAMS:
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
async def climate_attribute_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test the climate attribute condition with the 'any' behavior."""
    for condition_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for condition, condition_options, states in _ATTRIBUTE_CONDITION_ANY_PARAMS:
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
async def climate_attribute_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test the climate attribute condition with the 'all' behavior."""
    for condition_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for condition, condition_options, states in _ATTRIBUTE_CONDITION_ALL_PARAMS:
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
async def climate_numerical_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test the climate numerical condition with the 'any' behavior."""
    for condition_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for condition, condition_options, states in _NUMERICAL_CONDITION_ANY_PARAMS:
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
async def climate_numerical_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test the climate numerical condition with the 'all' behavior."""
    for condition_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for condition, condition_options, states in _NUMERICAL_CONDITION_ALL_PARAMS:
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
async def climate_numerical_condition_unit_conversion(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that the climate numerical condition converts units correctly."""
    _unit_celsius = {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS}
    _unit_fahrenheit = {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.FAHRENHEIT}
    _unit_invalid = {ATTR_UNIT_OF_MEASUREMENT: "not_a_valid_unit"}

    await assert_numerical_condition_unit_conversion(
        hass,
        condition="climate.target_temperature",
        entity_id="climate.test",
        pass_states=[{"state": HVACMode.AUTO, "attributes": {ATTR_TEMPERATURE: 25}}],
        fail_states=[
            {
                "state": HVACMode.AUTO,
                "attributes": {ATTR_TEMPERATURE: 20},
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


# Silence unused-import warning — ConditionStateDescription is part of the
# public test surface used by these helpers but not directly referenced.
_ = ConditionStateDescription
