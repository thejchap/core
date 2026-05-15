"""Test doorbell trigger."""

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.event import ATTR_EVENT_TYPE
from homeassistant.const import ATTR_DEVICE_CLASS, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from ._fixtures import (
    enable_labs_preview_features,
    target_events as target_events_fixture,
)

from tests.components.common import (
    arm_trigger,
    assert_trigger_gated_by_labs_flag,
    assert_trigger_options_supported,
    parametrize_target_entities,
    set_or_remove_state,
)
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def doorbell_triggers_gated_by_labs_flag(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the doorbell triggers are gated by the labs flag."""
    await assert_trigger_gated_by_labs_flag(
        hass,
        caplog,
        "doorbell.rang",
    )


@test
async def doorbell_trigger_options_validation(
    hass: HomeAssistant = Depends(_trigger_executor),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that doorbell triggers support the expected options."""
    await assert_trigger_options_supported(
        hass,
        "doorbell.rang",
        None,
        supports_behavior=False,
        supports_duration=False,
    )


_RING_STATE_BASE = {
    ATTR_DEVICE_CLASS: "doorbell",
    ATTR_EVENT_TYPE: "ring",
}

_RING_STATE_OTHER = {
    ATTR_DEVICE_CLASS: "doorbell",
    ATTR_EVENT_TYPE: "other_event",
}

_DOORBELL_RANG_STATE_SCENARIOS: list[tuple[str, list[dict[str, Any]]]] = [
    (
        "unavailable_then_ring",
        [
            {
                "included_state": {
                    "state": STATE_UNAVAILABLE,
                    "attributes": {ATTR_DEVICE_CLASS: "doorbell"},
                },
                "count": 0,
            },
            {
                "included_state": {
                    "state": "2026-01-01T00:00:00.000+00:00",
                    "attributes": _RING_STATE_BASE,
                },
                "count": 0,
            },
            {
                "included_state": {
                    "state": "2026-01-01T00:00:01.000+00:00",
                    "attributes": _RING_STATE_BASE,
                },
                "count": 1,
            },
        ],
    ),
    (
        "unknown_first_ring_triggers",
        [
            {
                "included_state": {
                    "state": STATE_UNKNOWN,
                    "attributes": {ATTR_DEVICE_CLASS: "doorbell"},
                },
                "count": 0,
            },
            {
                "included_state": {
                    "state": "2026-01-01T00:00:00.000+00:00",
                    "attributes": _RING_STATE_BASE,
                },
                "count": 1,
            },
            {
                "included_state": {
                    "state": "2026-01-01T00:00:01.000+00:00",
                    "attributes": _RING_STATE_BASE,
                },
                "count": 1,
            },
            {
                "included_state": {
                    "state": STATE_UNKNOWN,
                    "attributes": {ATTR_DEVICE_CLASS: "doorbell"},
                },
                "count": 0,
            },
        ],
    ),
    (
        "ring_again_different_timestamps",
        [
            {
                "included_state": {
                    "state": "2026-01-01T00:00:00.000+00:00",
                    "attributes": _RING_STATE_BASE,
                },
                "count": 0,
            },
            {
                "included_state": {
                    "state": "2026-01-01T00:00:01.000+00:00",
                    "attributes": _RING_STATE_BASE,
                },
                "count": 1,
            },
            {
                "included_state": {
                    "state": "2026-01-01T00:00:02.000+00:00",
                    "attributes": _RING_STATE_BASE,
                },
                "count": 1,
            },
        ],
    ),
    (
        "to_unavailable_skips_next",
        [
            {
                "included_state": {
                    "state": "2026-01-01T00:00:00.000+00:00",
                    "attributes": _RING_STATE_BASE,
                },
                "count": 0,
            },
            {
                "included_state": {
                    "state": STATE_UNAVAILABLE,
                    "attributes": {ATTR_DEVICE_CLASS: "doorbell"},
                },
                "count": 0,
            },
            {
                "included_state": {
                    "state": "2026-01-01T00:00:01.000+00:00",
                    "attributes": _RING_STATE_BASE,
                },
                "count": 0,
            },
            {
                "included_state": {
                    "state": "2026-01-01T00:00:02.000+00:00",
                    "attributes": _RING_STATE_BASE,
                },
                "count": 1,
            },
        ],
    ),
    (
        "non_ring_event_type_skipped",
        [
            {
                "included_state": {
                    "state": STATE_UNAVAILABLE,
                    "attributes": {ATTR_DEVICE_CLASS: "doorbell"},
                },
                "count": 0,
            },
            {
                "included_state": {
                    "state": "2026-01-01T00:00:00.000+00:00",
                    "attributes": _RING_STATE_OTHER,
                },
                "count": 0,
            },
            {
                "included_state": {
                    "state": "2026-01-01T00:00:01.000+00:00",
                    "attributes": _RING_STATE_BASE,
                },
                "count": 1,
            },
            {
                "included_state": {
                    "state": "2026-01-01T00:00:00.000+00:00",
                    "attributes": _RING_STATE_OTHER,
                },
                "count": 0,
            },
        ],
    ),
]

_TARGET_ENTITIES_PARAMS = parametrize_target_entities("event")


@test.cases(
    test.case(
        "unavailable_then_ring",
        scenario_idx=0,
    ),
    test.case(
        "unknown_first_ring_triggers",
        scenario_idx=1,
    ),
    test.case(
        "ring_again_different_timestamps",
        scenario_idx=2,
    ),
    test.case(
        "to_unavailable_skips_next",
        scenario_idx=3,
    ),
    test.case(
        "non_ring_event_type_skipped",
        scenario_idx=4,
    ),
)
async def doorbell_rang_trigger(
    scenario_idx: int,
    hass: HomeAssistant = Depends(_trigger_executor),
    _labs: None = Depends(enable_labs_preview_features),
    target_events: dict[str, list[str]] = Depends(target_events_fixture),
) -> None:
    """Test that the doorbell rang trigger fires when a doorbell ring event is received."""
    _, states = _DOORBELL_RANG_STATE_SCENARIOS[scenario_idx]
    # Cover all parametrize_target_entities target types within this scenario.
    for trigger_target_config, entity_id, entities_in_target in _TARGET_ENTITIES_PARAMS:
        calls: list[str] = []
        other_entity_ids = set(target_events["included_entities"]) - {entity_id}

        # Set all events to the initial state
        for eid in target_events["included_entities"]:
            set_or_remove_state(hass, eid, states[0]["included_state"])
            await hass.async_block_till_done()

        await arm_trigger(hass, "doorbell.rang", None, trigger_target_config, calls)

        for state in states[1:]:
            included_state = state["included_state"]
            set_or_remove_state(hass, entity_id, included_state)
            await hass.async_block_till_done()
            expect(len(calls)).to_equal(state["count"])
            for call in calls:
                expect(call).to_equal(entity_id)
            calls.clear()

            # Check if changing other events also triggers
            for other_entity_id in other_entity_ids:
                set_or_remove_state(hass, other_entity_id, included_state)
                await hass.async_block_till_done()
            expect(len(calls)).to_equal((entities_in_target - 1) * state["count"])
            calls.clear()
