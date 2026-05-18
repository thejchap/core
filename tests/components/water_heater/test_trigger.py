"""Test water heater trigger."""

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.water_heater import (
    STATE_ECO,
    STATE_ELECTRIC,
    STATE_GAS,
    STATE_HEAT_PUMP,
    STATE_HIGH_DEMAND,
    STATE_PERFORMANCE,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_OFF, STATE_ON, UnitOfTemperature
from homeassistant.core import HomeAssistant

from ._fixtures import (
    enable_labs_preview_features,
    target_water_heaters as target_water_heaters_fixture,
)

from tests.components.common import (
    TriggerStateDescription,
    assert_trigger_behavior_any,
    assert_trigger_behavior_first,
    assert_trigger_behavior_last,
    assert_trigger_gated_by_labs_flag,
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


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    return 0


ALL_ON_STATES = [
    STATE_ECO,
    STATE_ELECTRIC,
    STATE_GAS,
    STATE_HEAT_PUMP,
    STATE_HIGH_DEMAND,
    STATE_ON,
    STATE_PERFORMANCE,
]

ALL_STATES = [STATE_OFF, *ALL_ON_STATES]


@test.cases(
    test.case(
        "operation_mode_changed",
        trigger_key="water_heater.operation_mode_changed",
    ),
    test.case(
        "target_temperature_changed",
        trigger_key="water_heater.target_temperature_changed",
    ),
    test.case(
        "target_temperature_crossed_threshold",
        trigger_key="water_heater.target_temperature_crossed_threshold",
    ),
    test.case("turned_off", trigger_key="water_heater.turned_off"),
    test.case("turned_on", trigger_key="water_heater.turned_on"),
)
async def water_heater_triggers_gated_by_labs_flag(
    trigger_key: str,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the water heater triggers are gated by the labs flag."""
    await assert_trigger_gated_by_labs_flag(hass, caplog, trigger_key)


@test.cases(
    test.case(
        "turned_off",
        trigger_key="water_heater.turned_off",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "turned_on",
        trigger_key="water_heater.turned_on",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
)
async def water_heater_trigger_options_validation(
    trigger_key: str,
    base_options: dict[str, Any] | None,
    supports_behavior: bool,
    supports_duration: bool,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that water_heater triggers support the expected options."""
    await assert_trigger_options_supported(
        hass,
        trigger_key,
        base_options,
        supports_behavior=supports_behavior,
        supports_duration=supports_duration,
    )


_WATER_HEATER_TARGET_PARAMS = parametrize_target_entities("water_heater")

_STATE_TRIGGER_STATES = [
    *(
        param
        for mode in ALL_STATES
        for param in parametrize_trigger_states(
            trigger="water_heater.operation_mode_changed",
            trigger_options={"operation_mode": [mode]},
            target_states=[mode],
            other_states=[s for s in ALL_STATES if s != mode],
        )
    ),
    *parametrize_trigger_states(
        trigger="water_heater.operation_mode_changed",
        trigger_options={"operation_mode": [STATE_ECO, STATE_ELECTRIC]},
        target_states=[STATE_ECO, STATE_ELECTRIC],
        other_states=[s for s in ALL_STATES if s not in (STATE_ECO, STATE_ELECTRIC)],
    ),
    *parametrize_trigger_states(
        trigger="water_heater.turned_off",
        target_states=[STATE_OFF],
        other_states=ALL_ON_STATES,
    ),
    *parametrize_trigger_states(
        trigger="water_heater.turned_on",
        target_states=ALL_ON_STATES,
        other_states=[STATE_OFF],
    ),
]

_STATE_ATTRIBUTE_TRIGGER_STATES_ANY = [
    *parametrize_numerical_attribute_changed_trigger_states(
        "water_heater.target_temperature_changed",
        STATE_ECO,
        ATTR_TEMPERATURE,
        threshold_unit=UnitOfTemperature.CELSIUS,
        attribute_required=True,
    ),
    *parametrize_numerical_attribute_crossed_threshold_trigger_states(
        "water_heater.target_temperature_crossed_threshold",
        STATE_ECO,
        ATTR_TEMPERATURE,
        threshold_unit=UnitOfTemperature.CELSIUS,
        attribute_required=True,
    ),
]

_STATE_ATTRIBUTE_TRIGGER_STATES_FIRST_LAST = [
    *parametrize_numerical_attribute_crossed_threshold_trigger_states(
        "water_heater.target_temperature_crossed_threshold",
        STATE_ECO,
        ATTR_TEMPERATURE,
        threshold_unit=UnitOfTemperature.CELSIUS,
        attribute_required=True,
    ),
]


@test
async def water_heater_state_trigger_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_water_heaters: dict[str, list[str]] = Depends(target_water_heaters_fixture),
) -> None:
    """Test that the water heater state trigger fires when any water heater state changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _WATER_HEATER_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_TRIGGER_STATES:
            await assert_trigger_behavior_any(
                hass,
                target_entities=target_water_heaters,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def water_heater_state_attribute_trigger_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_water_heaters: dict[str, list[str]] = Depends(target_water_heaters_fixture),
) -> None:
    """Test that the water heater target temperature attribute triggers fire when any water heater's target temperature changes or crosses a threshold."""
    for trigger_target_config, entity_id, entities_in_target in _WATER_HEATER_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_ATTRIBUTE_TRIGGER_STATES_ANY:
            await assert_trigger_behavior_any(
                hass,
                target_entities=target_water_heaters,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def water_heater_state_trigger_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_water_heaters: dict[str, list[str]] = Depends(target_water_heaters_fixture),
) -> None:
    """Test that the water heater state trigger fires when the first water heater changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _WATER_HEATER_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_TRIGGER_STATES:
            await assert_trigger_behavior_first(
                hass,
                target_entities=target_water_heaters,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def water_heater_state_attribute_trigger_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_water_heaters: dict[str, list[str]] = Depends(target_water_heaters_fixture),
) -> None:
    """Test that the water heater attribute threshold trigger fires when the first water heater's target temperature crosses the configured threshold."""
    for trigger_target_config, entity_id, entities_in_target in _WATER_HEATER_TARGET_PARAMS:
        for (
            trigger,
            trigger_options,
            states,
        ) in _STATE_ATTRIBUTE_TRIGGER_STATES_FIRST_LAST:
            await assert_trigger_behavior_first(
                hass,
                target_entities=target_water_heaters,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def water_heater_state_trigger_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_water_heaters: dict[str, list[str]] = Depends(target_water_heaters_fixture),
) -> None:
    """Test that the water heater state trigger fires when the last water heater changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _WATER_HEATER_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_TRIGGER_STATES:
            await assert_trigger_behavior_last(
                hass,
                target_entities=target_water_heaters,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def water_heater_state_attribute_trigger_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_water_heaters: dict[str, list[str]] = Depends(target_water_heaters_fixture),
) -> None:
    """Test that the water heater trigger fires when the last water heater's target temperature crosses the configured threshold."""
    for trigger_target_config, entity_id, entities_in_target in _WATER_HEATER_TARGET_PARAMS:
        for (
            trigger,
            trigger_options,
            states,
        ) in _STATE_ATTRIBUTE_TRIGGER_STATES_FIRST_LAST:
            await assert_trigger_behavior_last(
                hass,
                target_entities=target_water_heaters,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


# Silence unused-import warnings for re-exports.
_ = TriggerStateDescription
_ = expect
