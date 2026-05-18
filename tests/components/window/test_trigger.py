"""Test window trigger."""

from typing import Any

from tryke import Depends, fixture, test

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.cover import ATTR_IS_CLOSED, CoverDeviceClass, CoverState
from homeassistant.const import ATTR_DEVICE_CLASS, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant

from ._fixtures import (
    enable_labs_preview_features,
    target_binary_sensors as target_binary_sensors_fixture,
    target_covers as target_covers_fixture,
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


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    return 0


@test.cases(
    test.case("opened", trigger_key="window.opened"),
    test.case("closed", trigger_key="window.closed"),
)
async def window_triggers_gated_by_labs_flag(
    trigger_key: str,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the window triggers are gated by the labs flag."""
    await assert_trigger_gated_by_labs_flag(hass, caplog, trigger_key)


@test.cases(
    test.case(
        "closed",
        trigger_key="window.closed",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "opened",
        trigger_key="window.opened",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
)
async def window_trigger_options_validation(
    trigger_key: str,
    base_options: dict[str, Any] | None,
    supports_behavior: bool,
    supports_duration: bool,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that window triggers support the expected options."""
    await assert_trigger_options_supported(
        hass,
        trigger_key,
        base_options,
        supports_behavior=supports_behavior,
        supports_duration=supports_duration,
    )


_BINARY_SENSOR_TARGET_PARAMS = parametrize_target_entities("binary_sensor")
_COVER_TARGET_PARAMS = parametrize_target_entities("cover")

_BINARY_SENSOR_STATES = [
    *parametrize_trigger_states(
        trigger="window.opened",
        target_states=[STATE_ON],
        other_states=[STATE_OFF],
        required_filter_attributes={
            ATTR_DEVICE_CLASS: BinarySensorDeviceClass.WINDOW
        },
        trigger_from_none=False,
    ),
    *parametrize_trigger_states(
        trigger="window.closed",
        target_states=[STATE_OFF],
        other_states=[STATE_ON],
        required_filter_attributes={
            ATTR_DEVICE_CLASS: BinarySensorDeviceClass.WINDOW
        },
        trigger_from_none=False,
    ),
]

_COVER_STATES = [
    *parametrize_trigger_states(
        trigger="window.opened",
        target_states=[
            (CoverState.OPEN, {ATTR_IS_CLOSED: False}),
            (CoverState.OPENING, {ATTR_IS_CLOSED: False}),
        ],
        other_states=[
            (CoverState.CLOSED, {ATTR_IS_CLOSED: True}),
            (CoverState.CLOSING, {ATTR_IS_CLOSED: True}),
        ],
        extra_invalid_states=[
            (CoverState.OPEN, {ATTR_IS_CLOSED: None}),
            (CoverState.OPEN, {}),
        ],
        required_filter_attributes={ATTR_DEVICE_CLASS: CoverDeviceClass.WINDOW},
        trigger_from_none=False,
    ),
    *parametrize_trigger_states(
        trigger="window.closed",
        target_states=[
            (CoverState.CLOSED, {ATTR_IS_CLOSED: True}),
            (CoverState.CLOSING, {ATTR_IS_CLOSED: True}),
        ],
        other_states=[
            (CoverState.OPEN, {ATTR_IS_CLOSED: False}),
            (CoverState.OPENING, {ATTR_IS_CLOSED: False}),
            (CoverState.CLOSING, {ATTR_IS_CLOSED: False}),
        ],
        extra_invalid_states=[
            (CoverState.OPEN, {ATTR_IS_CLOSED: None}),
            (CoverState.OPEN, {}),
        ],
        required_filter_attributes={ATTR_DEVICE_CLASS: CoverDeviceClass.WINDOW},
        trigger_from_none=False,
    ),
]


@test
async def window_trigger_binary_sensor_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_binary_sensors: dict[str, list[str]] = Depends(target_binary_sensors_fixture),
) -> None:
    """Test window trigger fires for binary_sensor entities with device_class window."""
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
async def window_trigger_cover_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_covers: dict[str, list[str]] = Depends(target_covers_fixture),
) -> None:
    """Test window trigger fires for cover entities with device_class window."""
    for trigger_target_config, entity_id, entities_in_target in _COVER_TARGET_PARAMS:
        for trigger, trigger_options, states in _COVER_STATES:
            await assert_trigger_behavior_any(
                hass,
                target_entities=target_covers,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def window_trigger_binary_sensor_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_binary_sensors: dict[str, list[str]] = Depends(target_binary_sensors_fixture),
) -> None:
    """Test window trigger fires on the first binary_sensor state change."""
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
async def window_trigger_binary_sensor_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_binary_sensors: dict[str, list[str]] = Depends(target_binary_sensors_fixture),
) -> None:
    """Test window trigger fires when the last binary_sensor changes state."""
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


@test
async def window_trigger_cover_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_covers: dict[str, list[str]] = Depends(target_covers_fixture),
) -> None:
    """Test window trigger fires on the first cover state change."""
    for trigger_target_config, entity_id, entities_in_target in _COVER_TARGET_PARAMS:
        for trigger, trigger_options, states in _COVER_STATES:
            await assert_trigger_behavior_first(
                hass,
                target_entities=target_covers,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def window_trigger_cover_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_covers: dict[str, list[str]] = Depends(target_covers_fixture),
) -> None:
    """Test window trigger fires when the last cover changes state."""
    for trigger_target_config, entity_id, entities_in_target in _COVER_TARGET_PARAMS:
        for trigger, trigger_options, states in _COVER_STATES:
            await assert_trigger_behavior_last(
                hass,
                target_entities=target_covers,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


# Silence unused-import warning — TriggerStateDescription is part of the
# public test surface used by these helpers but not directly referenced.
_ = TriggerStateDescription
