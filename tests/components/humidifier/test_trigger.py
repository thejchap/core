"""Test humidifier trigger."""

from typing import Any

from tryke import Depends, fixture, test
import voluptuous as vol

from homeassistant.components.humidifier.const import (
    ATTR_ACTION,
    HumidifierAction,
    HumidifierEntityFeature,
)
from homeassistant.components.humidifier.trigger import CONF_MODE
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
from homeassistant.helpers.trigger import async_validate_trigger_config

from ._fixtures import (
    enable_labs_preview_features,
    target_humidifiers as target_humidifiers_fixture,
)

from tests.components.common import (
    TriggerStateDescription,
    assert_trigger_behavior_any,
    assert_trigger_behavior_first,
    assert_trigger_behavior_last,
    assert_trigger_gated_by_labs_flag,
    assert_trigger_options_supported,
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
    test.case("mode_changed", trigger_key="humidifier.mode_changed"),
    test.case("started_drying", trigger_key="humidifier.started_drying"),
    test.case("started_humidifying", trigger_key="humidifier.started_humidifying"),
    test.case("turned_off", trigger_key="humidifier.turned_off"),
    test.case("turned_on", trigger_key="humidifier.turned_on"),
)
async def humidifier_triggers_gated_by_labs_flag(
    trigger_key: str,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the humidifier triggers are gated by the labs flag."""
    await assert_trigger_gated_by_labs_flag(hass, caplog, trigger_key)


@test.cases(
    test.case(
        "started_drying",
        trigger_key="humidifier.started_drying",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "started_humidifying",
        trigger_key="humidifier.started_humidifying",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "turned_on",
        trigger_key="humidifier.turned_on",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "turned_off",
        trigger_key="humidifier.turned_off",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
)
async def humidifier_trigger_options_validation(
    trigger_key: str,
    base_options: dict[str, Any] | None,
    supports_behavior: bool,
    supports_duration: bool,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that humidifier triggers support the expected options."""
    await assert_trigger_options_supported(
        hass,
        trigger_key,
        base_options,
        supports_behavior=supports_behavior,
        supports_duration=supports_duration,
    )


_HUMIDIFIER_TARGET_PARAMS = parametrize_target_entities("humidifier")

_STATE_TRIGGER_STATES = [
    *parametrize_trigger_states(
        trigger="humidifier.turned_on",
        target_states=[STATE_ON],
        other_states=[STATE_OFF],
    ),
    *parametrize_trigger_states(
        trigger="humidifier.turned_off",
        target_states=[STATE_OFF],
        other_states=[STATE_ON],
    ),
]

_STATE_ATTRIBUTE_TRIGGER_STATES = [
    *parametrize_trigger_states(
        trigger="humidifier.started_drying",
        target_states=[(STATE_ON, {ATTR_ACTION: HumidifierAction.DRYING})],
        other_states=[(STATE_ON, {ATTR_ACTION: HumidifierAction.IDLE})],
    ),
    *parametrize_trigger_states(
        trigger="humidifier.started_humidifying",
        target_states=[(STATE_ON, {ATTR_ACTION: HumidifierAction.HUMIDIFYING})],
        other_states=[(STATE_ON, {ATTR_ACTION: HumidifierAction.IDLE})],
    ),
    *parametrize_trigger_states(
        trigger="humidifier.mode_changed",
        trigger_options={CONF_MODE: ["eco", "sleep"]},
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
        trigger_from_none=False,
    ),
]


@test
async def humidifier_state_trigger_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test that the humidifier state trigger fires when any humidifier state changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_TRIGGER_STATES:
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
async def humidifier_state_attribute_trigger_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test that the humidifier state trigger fires when any humidifier state changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_ATTRIBUTE_TRIGGER_STATES:
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
async def humidifier_state_trigger_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test that the humidifier state trigger fires when the first humidifier changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_TRIGGER_STATES:
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
async def humidifier_state_attribute_trigger_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test that the humidifier state trigger fires when the first humidifier state changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_ATTRIBUTE_TRIGGER_STATES:
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
async def humidifier_state_trigger_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test that the humidifier state trigger fires when the last humidifier changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_TRIGGER_STATES:
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


@test
async def humidifier_state_attribute_trigger_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_humidifiers: dict[str, list[str]] = Depends(target_humidifiers_fixture),
) -> None:
    """Test that the humidifier state trigger fires when the last humidifier state changes to a specific state."""
    for trigger_target_config, entity_id, entities_in_target in _HUMIDIFIER_TARGET_PARAMS:
        for trigger, trigger_options, states in _STATE_ATTRIBUTE_TRIGGER_STATES:
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


@test.cases(
    test.case(
        "mode_list",
        trigger="humidifier.mode_changed",
        trigger_options={CONF_MODE: ["eco", "sleep"]},
    ),
    test.case(
        "mode_str",
        trigger="humidifier.mode_changed",
        trigger_options={CONF_MODE: "eco"},
    ),
)
async def humidifier_mode_changed_trigger_validation_valid(
    trigger: str,
    trigger_options: dict[str, Any],
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test humidifier mode_changed trigger config accepts valid options."""
    await async_validate_trigger_config(
        hass,
        [
            {
                "platform": trigger,
                CONF_TARGET: {CONF_ENTITY_ID: "humidifier.test"},
                CONF_OPTIONS: trigger_options,
            }
        ],
    )


@test.cases(
    test.case(
        "mode_empty_list",
        trigger="humidifier.mode_changed",
        trigger_options={CONF_MODE: []},
    ),
    test.case(
        "mode_missing",
        trigger="humidifier.mode_changed",
        trigger_options={},
    ),
)
async def humidifier_mode_changed_trigger_validation_invalid(
    trigger: str,
    trigger_options: dict[str, Any],
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test humidifier mode_changed trigger config rejects invalid options."""
    async with expect_raises_async(vol.Invalid):
        await async_validate_trigger_config(
            hass,
            [
                {
                    "platform": trigger,
                    CONF_TARGET: {CONF_ENTITY_ID: "humidifier.test"},
                    CONF_OPTIONS: trigger_options,
                }
            ],
        )


# Silence unused-import warning — TriggerStateDescription is part of the
# public test surface used by these helpers but not directly referenced.
_ = TriggerStateDescription
