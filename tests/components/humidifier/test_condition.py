"""Test humidifier conditions."""

from typing import Any

from tryke import Depends, fixture, test
import voluptuous as vol

from homeassistant.components.humidifier.condition import CONF_MODE
from homeassistant.components.humidifier.const import (
    ATTR_ACTION,
    ATTR_HUMIDITY,
    HumidifierAction,
    HumidifierEntityFeature,
)
from homeassistant.const import (
    ATTR_MODE,
    ATTR_SUPPORTED_FEATURES,
    CONF_ENTITY_ID,
    CONF_OPTIONS,
    CONF_TARGET,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.condition import async_validate_condition_config

from ._fixtures import (
    enable_labs_preview_features,
    target_humidifiers as target_humidifiers_fixture,
)

from tests.components.common import (
    ConditionStateDescription,
    assert_condition_behavior_all,
    assert_condition_behavior_any,
    assert_condition_gated_by_labs_flag,
    assert_condition_options_supported,
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
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    return 0


@test.cases(
    test.case("is_off", condition="humidifier.is_off"),
    test.case("is_on", condition="humidifier.is_on"),
    test.case("is_drying", condition="humidifier.is_drying"),
    test.case("is_humidifying", condition="humidifier.is_humidifying"),
    test.case("is_mode", condition="humidifier.is_mode"),
    test.case("is_target_humidity", condition="humidifier.is_target_humidity"),
)
async def humidifier_conditions_gated_by_labs_flag(
    condition: str,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the humidifier conditions are gated by the labs flag."""
    await assert_condition_gated_by_labs_flag(hass, caplog, condition)


@test.cases(
    test.case(
        "is_off",
        condition_key="humidifier.is_off",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_on",
        condition_key="humidifier.is_on",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_drying",
        condition_key="humidifier.is_drying",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "is_humidifying",
        condition_key="humidifier.is_humidifying",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
)
async def humidifier_condition_options_validation(
    condition_key: str,
    base_options: dict[str, Any] | None,
    supports_behavior: bool,
    supports_duration: bool,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that humidifier conditions support the expected options."""
    await assert_condition_options_supported(
        hass,
        condition_key,
        base_options,
        supports_behavior=supports_behavior,
        supports_duration=supports_duration,
    )


_HUMIDIFIER_TARGET_PARAMS = parametrize_target_entities("humidifier")

_STATE_CONDITION_ANY_PARAMS = [
    *parametrize_condition_states_any(
        condition="humidifier.is_off",
        target_states=[STATE_OFF],
        other_states=[STATE_ON],
    ),
    *parametrize_condition_states_any(
        condition="humidifier.is_on",
        target_states=[STATE_ON],
        other_states=[STATE_OFF],
    ),
]

_STATE_CONDITION_ALL_PARAMS = [
    *parametrize_condition_states_all(
        condition="humidifier.is_off",
        target_states=[STATE_OFF],
        other_states=[STATE_ON],
    ),
    *parametrize_condition_states_all(
        condition="humidifier.is_on",
        target_states=[STATE_ON],
        other_states=[STATE_OFF],
    ),
]

_ATTRIBUTE_CONDITION_ANY_PARAMS = [
    *parametrize_condition_states_any(
        condition="humidifier.is_drying",
        target_states=[(STATE_ON, {ATTR_ACTION: HumidifierAction.DRYING})],
        other_states=[(STATE_ON, {ATTR_ACTION: HumidifierAction.IDLE})],
    ),
    *parametrize_condition_states_any(
        condition="humidifier.is_humidifying",
        target_states=[(STATE_ON, {ATTR_ACTION: HumidifierAction.HUMIDIFYING})],
        other_states=[(STATE_ON, {ATTR_ACTION: HumidifierAction.IDLE})],
    ),
    *parametrize_condition_states_any(
        condition="humidifier.is_mode",
        condition_options={CONF_MODE: ["eco", "sleep"]},
        target_states=[
            (STATE_ON, {ATTR_MODE: "eco"}),
            (STATE_ON, {ATTR_MODE: "sleep"}),
        ],
        other_states=[
            (STATE_ON, {ATTR_MODE: "normal"}),
        ],
        required_filter_attributes={
            ATTR_SUPPORTED_FEATURES: HumidifierEntityFeature.MODES
        },
    ),
]

_ATTRIBUTE_CONDITION_ALL_PARAMS = [
    *parametrize_condition_states_all(
        condition="humidifier.is_drying",
        target_states=[(STATE_ON, {ATTR_ACTION: HumidifierAction.DRYING})],
        other_states=[(STATE_ON, {ATTR_ACTION: HumidifierAction.IDLE})],
    ),
    *parametrize_condition_states_all(
        condition="humidifier.is_humidifying",
        target_states=[(STATE_ON, {ATTR_ACTION: HumidifierAction.HUMIDIFYING})],
        other_states=[(STATE_ON, {ATTR_ACTION: HumidifierAction.IDLE})],
    ),
    *parametrize_condition_states_all(
        condition="humidifier.is_mode",
        condition_options={CONF_MODE: ["eco", "sleep"]},
        target_states=[
            (STATE_ON, {ATTR_MODE: "eco"}),
            (STATE_ON, {ATTR_MODE: "sleep"}),
        ],
        other_states=[
            (STATE_ON, {ATTR_MODE: "normal"}),
        ],
        required_filter_attributes={
            ATTR_SUPPORTED_FEATURES: HumidifierEntityFeature.MODES
        },
    ),
]

_NUMERICAL_CONDITION_ANY_PARAMS = (
    parametrize_numerical_attribute_condition_above_below_any(
        "humidifier.is_target_humidity",
        STATE_ON,
        ATTR_HUMIDITY,
        attribute_required=True,
    )
)
_NUMERICAL_CONDITION_ALL_PARAMS = (
    parametrize_numerical_attribute_condition_above_below_all(
        "humidifier.is_target_humidity",
        STATE_ON,
        ATTR_HUMIDITY,
        attribute_required=True,
    )
)


@test
async def humidifier_state_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test the humidifier state condition with the 'any' behavior."""
    for condition_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for condition, condition_options, states in _STATE_CONDITION_ANY_PARAMS:
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
async def humidifier_state_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test the humidifier state condition with the 'all' behavior."""
    for condition_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for condition, condition_options, states in _STATE_CONDITION_ALL_PARAMS:
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
async def humidifier_attribute_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test the humidifier attribute condition with the 'any' behavior."""
    for condition_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for condition, condition_options, states in _ATTRIBUTE_CONDITION_ANY_PARAMS:
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
async def humidifier_attribute_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test the humidifier attribute condition with the 'all' behavior."""
    for condition_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for condition, condition_options, states in _ATTRIBUTE_CONDITION_ALL_PARAMS:
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
async def humidifier_numerical_condition_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test the humidifier numerical condition with the 'any' behavior."""
    for condition_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for condition, condition_options, states in _NUMERICAL_CONDITION_ANY_PARAMS:
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
async def humidifier_numerical_condition_behavior_all(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test the humidifier numerical condition with the 'all' behavior."""
    for condition_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for condition, condition_options, states in _NUMERICAL_CONDITION_ALL_PARAMS:
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


@test.cases(
    test.case(
        "mode_list",
        condition="humidifier.is_mode",
        condition_options={CONF_MODE: ["eco", "sleep"]},
    ),
    test.case(
        "mode_str",
        condition="humidifier.is_mode",
        condition_options={CONF_MODE: "eco"},
    ),
)
async def humidifier_is_mode_condition_validation_valid(
    condition: str,
    condition_options: dict[str, Any],
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test humidifier is_mode condition config accepts valid options."""
    await async_validate_condition_config(
        hass,
        {
            "condition": condition,
            CONF_TARGET: {CONF_ENTITY_ID: "humidifier.test"},
            CONF_OPTIONS: condition_options,
        },
    )


@test.cases(
    test.case(
        "mode_empty_list",
        condition="humidifier.is_mode",
        condition_options={CONF_MODE: []},
    ),
    test.case(
        "mode_missing",
        condition="humidifier.is_mode",
        condition_options={},
    ),
)
async def humidifier_is_mode_condition_validation_invalid(
    condition: str,
    condition_options: dict[str, Any],
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test humidifier is_mode condition config rejects invalid options."""
    async with expect_raises_async(vol.Invalid):
        await async_validate_condition_config(
            hass,
            {
                "condition": condition,
                CONF_TARGET: {CONF_ENTITY_ID: "humidifier.test"},
                CONF_OPTIONS: condition_options,
            },
        )


# Silence unused-import warning — ConditionStateDescription is part of the
# public test surface used by these helpers but not directly referenced.
_ = ConditionStateDescription
