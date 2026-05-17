"""Test climate trigger."""

from typing import Any

import voluptuous as vol

from tryke import Depends, expect, fixture, test

from homeassistant.components.climate.const import (
    ATTR_HUMIDITY,
    ATTR_HVAC_ACTION,
    HVACAction,
    HVACMode,
)
from homeassistant.components.climate.trigger import CONF_HVAC_MODE
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_ENTITY_ID,
    CONF_OPTIONS,
    CONF_TARGET,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.trigger import async_validate_trigger_config

from ._fixtures import (
    enable_labs_preview_features,
    target_climates as target_climates_fixture,
)

from tests.components.common import (
    TriggerStateDescription,
    assert_trigger_behavior_any,
    assert_trigger_behavior_first,
    assert_trigger_behavior_last,
    assert_trigger_gated_by_labs_flag,
    assert_trigger_options_supported,
    other_states,
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
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    return 0


@test.cases(
    test.case("hvac_mode_changed", trigger_key="climate.hvac_mode_changed"),
    test.case(
        "target_humidity_changed", trigger_key="climate.target_humidity_changed"
    ),
    test.case(
        "target_humidity_crossed_threshold",
        trigger_key="climate.target_humidity_crossed_threshold",
    ),
    test.case(
        "target_temperature_changed",
        trigger_key="climate.target_temperature_changed",
    ),
    test.case(
        "target_temperature_crossed_threshold",
        trigger_key="climate.target_temperature_crossed_threshold",
    ),
    test.case("turned_off", trigger_key="climate.turned_off"),
    test.case("turned_on", trigger_key="climate.turned_on"),
    test.case("started_cooling", trigger_key="climate.started_cooling"),
    test.case("started_drying", trigger_key="climate.started_drying"),
    test.case("started_heating", trigger_key="climate.started_heating"),
)
async def climate_triggers_gated_by_labs_flag(
    trigger_key: str,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the climate triggers are gated by the labs flag."""
    await assert_trigger_gated_by_labs_flag(hass, caplog, trigger_key)


@test.cases(
    test.case(
        "started_cooling",
        trigger_key="climate.started_cooling",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "started_drying",
        trigger_key="climate.started_drying",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "started_heating",
        trigger_key="climate.started_heating",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "turned_off",
        trigger_key="climate.turned_off",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "turned_on",
        trigger_key="climate.turned_on",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
)
async def climate_trigger_options_validation(
    trigger_key: str,
    base_options: dict[str, Any] | None,
    supports_behavior: bool,
    supports_duration: bool,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that climate triggers support the expected options."""
    await assert_trigger_options_supported(
        hass,
        trigger_key,
        base_options,
        supports_behavior=supports_behavior,
        supports_duration=supports_duration,
    )


async def _validate_trigger(
    hass: HomeAssistant, trigger: str, trigger_options: dict[str, Any]
) -> None:
    await async_validate_trigger_config(
        hass,
        [
            {
                "platform": trigger,
                CONF_TARGET: {CONF_ENTITY_ID: "climate.test_climate"},
                CONF_OPTIONS: trigger_options,
            }
        ],
    )


@test.cases(
    test.case(
        "hvac_mode_list_valid",
        trigger="climate.hvac_mode_changed",
        trigger_options={CONF_HVAC_MODE: ["heat", "cool"]},
        should_raise=False,
    ),
    test.case(
        "hvac_mode_str_valid",
        trigger="climate.hvac_mode_changed",
        trigger_options={CONF_HVAC_MODE: "heat"},
        should_raise=False,
    ),
    test.case(
        "hvac_mode_empty_list_invalid",
        trigger="climate.hvac_mode_changed",
        trigger_options={CONF_HVAC_MODE: []},
        should_raise=True,
    ),
    test.case(
        "hvac_mode_missing_invalid",
        trigger="climate.hvac_mode_changed",
        trigger_options={},
        should_raise=True,
    ),
    test.case(
        "hvac_mode_invalid_value",
        trigger="climate.hvac_mode_changed",
        trigger_options={CONF_HVAC_MODE: ["invalid_mode"]},
        should_raise=True,
    ),
)
async def climate_trigger_validation(
    trigger: str,
    trigger_options: dict[str, Any],
    should_raise: bool,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test climate trigger config validation."""
    if should_raise:
        async with expect_raises_async(vol.Invalid):
            await _validate_trigger(hass, trigger, trigger_options)
    else:
        await _validate_trigger(hass, trigger, trigger_options)


_CLIMATE_TARGET_PARAMS = parametrize_target_entities("climate")

_STATE_TRIGGER_STATES = [
    *parametrize_trigger_states(
        trigger="climate.hvac_mode_changed",
        trigger_options={CONF_HVAC_MODE: ["heat", "cool"]},
        target_states=[HVACMode.HEAT, HVACMode.COOL],
        other_states=other_states([HVACMode.HEAT, HVACMode.COOL]),
    ),
    *parametrize_trigger_states(
        trigger="climate.turned_off",
        target_states=[HVACMode.OFF],
        other_states=other_states(HVACMode.OFF),
    ),
    *parametrize_trigger_states(
        trigger="climate.turned_on",
        target_states=[
            HVACMode.AUTO,
            HVACMode.COOL,
            HVACMode.DRY,
            HVACMode.FAN_ONLY,
            HVACMode.HEAT,
            HVACMode.HEAT_COOL,
        ],
        other_states=[
            HVACMode.OFF,
        ],
    ),
]

_STATE_ATTRIBUTE_TRIGGER_STATES_ANY = [
    *parametrize_numerical_attribute_changed_trigger_states(
        "climate.target_humidity_changed",
        HVACMode.AUTO,
        ATTR_HUMIDITY,
        attribute_required=True,
    ),
    *parametrize_numerical_attribute_changed_trigger_states(
        "climate.target_temperature_changed",
        HVACMode.AUTO,
        ATTR_TEMPERATURE,
        threshold_unit=UnitOfTemperature.CELSIUS,
        attribute_required=True,
    ),
    *parametrize_numerical_attribute_crossed_threshold_trigger_states(
        "climate.target_humidity_crossed_threshold",
        HVACMode.AUTO,
        ATTR_HUMIDITY,
        attribute_required=True,
    ),
    *parametrize_numerical_attribute_crossed_threshold_trigger_states(
        "climate.target_temperature_crossed_threshold",
        HVACMode.AUTO,
        ATTR_TEMPERATURE,
        threshold_unit=UnitOfTemperature.CELSIUS,
        attribute_required=True,
    ),
    *parametrize_trigger_states(
        trigger="climate.started_cooling",
        target_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.COOLING})],
        other_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.IDLE})],
    ),
    *parametrize_trigger_states(
        trigger="climate.started_drying",
        target_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.DRYING})],
        other_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.IDLE})],
    ),
    *parametrize_trigger_states(
        trigger="climate.started_heating",
        target_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.HEATING})],
        other_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.IDLE})],
    ),
]

_STATE_ATTRIBUTE_TRIGGER_STATES_FIRST_LAST = [
    *parametrize_numerical_attribute_crossed_threshold_trigger_states(
        "climate.target_humidity_crossed_threshold",
        HVACMode.AUTO,
        ATTR_HUMIDITY,
        attribute_required=True,
    ),
    *parametrize_numerical_attribute_crossed_threshold_trigger_states(
        "climate.target_temperature_crossed_threshold",
        HVACMode.AUTO,
        ATTR_TEMPERATURE,
        threshold_unit=UnitOfTemperature.CELSIUS,
        attribute_required=True,
    ),
    *parametrize_trigger_states(
        trigger="climate.started_cooling",
        target_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.COOLING})],
        other_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.IDLE})],
    ),
    *parametrize_trigger_states(
        trigger="climate.started_drying",
        target_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.DRYING})],
        other_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.IDLE})],
    ),
    *parametrize_trigger_states(
        trigger="climate.started_heating",
        target_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.HEATING})],
        other_states=[(HVACMode.AUTO, {ATTR_HVAC_ACTION: HVACAction.IDLE})],
    ),
]


@test
async def climate_state_trigger_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test that the climate state trigger fires when any climate state changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_TRIGGER_STATES:
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
async def climate_state_attribute_trigger_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test that the climate state trigger fires when any climate state changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_ATTRIBUTE_TRIGGER_STATES_ANY:
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
async def climate_state_trigger_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test that the climate state trigger fires when the first climate changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_TRIGGER_STATES:
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
async def climate_state_attribute_trigger_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test that the climate state trigger fires when the first climate state changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for (
            trigger,
            trigger_options,
            states,
        ) in _STATE_ATTRIBUTE_TRIGGER_STATES_FIRST_LAST:
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
async def climate_state_trigger_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test that the climate state trigger fires when the last climate changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_TRIGGER_STATES:
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


@test
async def climate_state_attribute_trigger_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_climates: dict[str, list[str]] = Depends(target_climates_fixture),
) -> None:
    """Test that the climate state trigger fires when the last climate state changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _CLIMATE_TARGET_PARAMS:
        for (
            trigger,
            trigger_options,
            states,
        ) in _STATE_ATTRIBUTE_TRIGGER_STATES_FIRST_LAST:
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


# Silence unused-import warning — these are part of the public test surface
# used by these helpers but not directly referenced.
_ = TriggerStateDescription
_ = expect
