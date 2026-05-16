"""Test timer triggers."""

from datetime import timedelta
import logging
from typing import Any

from freezegun.api import FrozenDateTimeFactory
import voluptuous as vol

from tryke import Depends, expect, fixture, test

from homeassistant.components.timer import (
    ATTR_FINISHES_AT,
    ATTR_LAST_TRANSITION,
    DOMAIN,
    STATUS_ACTIVE,
    STATUS_IDLE,
    STATUS_PAUSED,
)
from homeassistant.const import (
    ATTR_LABEL_ID,
    CONF_ENTITY_ID,
    CONF_OPTIONS,
    CONF_PLATFORM,
    CONF_TARGET,
)
from homeassistant.core import Context, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er, label_registry as lr
from homeassistant.helpers.trigger import (
    async_initialize_triggers,
    async_validate_trigger_config,
)
from homeassistant.helpers.typing import TemplateVarsType
from homeassistant.util import dt as dt_util

from ._fixtures import (
    enable_labs_preview_features,
    target_timers as target_timers_fixture,
)

from tests.common import async_fire_time_changed
from tests.components.common import (
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
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    return 0


@test.cases(
    test.case("cancelled", trigger_key="timer.cancelled"),
    test.case("finished", trigger_key="timer.finished"),
    test.case("paused", trigger_key="timer.paused"),
    test.case("restarted", trigger_key="timer.restarted"),
    test.case("started", trigger_key="timer.started"),
    test.case("time_remaining", trigger_key="timer.time_remaining"),
)
async def timer_triggers_gated_by_labs_flag(
    trigger_key: str,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the timer triggers are gated by the labs flag."""
    await assert_trigger_gated_by_labs_flag(hass, caplog, trigger_key)


@test.cases(
    test.case(
        "cancelled",
        trigger_key="timer.cancelled",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "finished",
        trigger_key="timer.finished",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "paused",
        trigger_key="timer.paused",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "restarted",
        trigger_key="timer.restarted",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "started",
        trigger_key="timer.started",
        base_options={},
        supports_behavior=True,
        supports_duration=True,
    ),
    test.case(
        "time_remaining",
        trigger_key="timer.time_remaining",
        base_options={"remaining": {"hours": 1}},
        supports_behavior=False,
        supports_duration=False,
    ),
)
async def timer_trigger_options_validation(
    trigger_key: str,
    base_options: dict[str, Any] | None,
    supports_behavior: bool,
    supports_duration: bool,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test that timer triggers support the expected options."""
    await assert_trigger_options_supported(
        hass,
        trigger_key,
        base_options,
        supports_behavior=supports_behavior,
        supports_duration=supports_duration,
    )


_TARGET_ENTITIES_PARAMS = parametrize_target_entities(DOMAIN)

_BEHAVIOR_STATES = [
    *parametrize_trigger_states(
        trigger="timer.cancelled",
        target_states=[(STATUS_IDLE, {ATTR_LAST_TRANSITION: "cancelled"})],
        other_states=[(STATUS_ACTIVE, {ATTR_LAST_TRANSITION: "started"})],
    ),
    *parametrize_trigger_states(
        trigger="timer.finished",
        target_states=[(STATUS_IDLE, {ATTR_LAST_TRANSITION: "finished"})],
        other_states=[(STATUS_ACTIVE, {ATTR_LAST_TRANSITION: "started"})],
    ),
    *parametrize_trigger_states(
        trigger="timer.paused",
        target_states=[(STATUS_PAUSED, {ATTR_LAST_TRANSITION: "paused"})],
        other_states=[(STATUS_ACTIVE, {ATTR_LAST_TRANSITION: "started"})],
    ),
    *parametrize_trigger_states(
        trigger="timer.restarted",
        target_states=[(STATUS_ACTIVE, {ATTR_LAST_TRANSITION: "restarted"})],
        other_states=[(STATUS_ACTIVE, {ATTR_LAST_TRANSITION: "started"})],
    ),
    *parametrize_trigger_states(
        trigger="timer.started",
        target_states=[(STATUS_ACTIVE, {ATTR_LAST_TRANSITION: "started"})],
        other_states=[(STATUS_IDLE, {ATTR_LAST_TRANSITION: "cancelled"})],
    ),
]


@test
async def timer_trigger_behavior_any(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_timers: dict[str, list[str]] = Depends(target_timers_fixture),
) -> None:
    """Test that the timer trigger fires when any timer's last_transition changes to a specific value."""
    for trigger_target_config, entity_id, entities_in_target in _TARGET_ENTITIES_PARAMS:
        for trigger, trigger_options, states in _BEHAVIOR_STATES:
            await assert_trigger_behavior_any(
                hass,
                target_entities=target_timers,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def timer_trigger_behavior_first(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_timers: dict[str, list[str]] = Depends(target_timers_fixture),
) -> None:
    """Test that the timer trigger fires when the first timer's last_transition changes to a specific value."""
    for trigger_target_config, entity_id, entities_in_target in _TARGET_ENTITIES_PARAMS:
        for trigger, trigger_options, states in _BEHAVIOR_STATES:
            await assert_trigger_behavior_first(
                hass,
                target_entities=target_timers,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


@test
async def timer_trigger_behavior_last(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    target_timers: dict[str, list[str]] = Depends(target_timers_fixture),
) -> None:
    """Test that the timer trigger fires when the last timer's last_transition changes to a specific value."""
    for trigger_target_config, entity_id, entities_in_target in _TARGET_ENTITIES_PARAMS:
        for trigger, trigger_options, states in _BEHAVIOR_STATES:
            await assert_trigger_behavior_last(
                hass,
                target_entities=target_timers,
                trigger_target_config=trigger_target_config,
                entity_id=entity_id,
                entities_in_target=entities_in_target,
                trigger=trigger,
                trigger_options=trigger_options,
                states=states,
            )


# --- time_remaining trigger tests ---


async def _arm_time_remaining_trigger(
    hass: HomeAssistant,
    entity_id: str,
    remaining: dict[str, int],
    calls: list[dict[str, Any]],
    *,
    target: dict[str, Any] | None = None,
) -> None:
    """Arm the time_remaining trigger."""
    trigger_config = await async_validate_trigger_config(
        hass,
        [
            {
                CONF_PLATFORM: "timer.time_remaining",
                CONF_TARGET: target or {CONF_ENTITY_ID: entity_id},
                CONF_OPTIONS: {"remaining": remaining},
            }
        ],
    )

    @callback
    def action(run_variables: TemplateVarsType, context: Context | None = None) -> None:
        calls.append(run_variables["trigger"])

    logger = logging.getLogger(__name__)

    def log_cb(level: int, msg: str, **kwargs: Any) -> None:
        logger._log(level, "%s", msg, **kwargs)

    await async_initialize_triggers(
        hass,
        trigger_config,
        action,
        domain="test",
        name="test_trigger",
        log_cb=log_cb,
    )


@test
async def time_remaining_trigger_validation(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
) -> None:
    """Test time_remaining trigger config validation."""
    # Valid config
    await async_validate_trigger_config(
        hass,
        [
            {
                CONF_PLATFORM: "timer.time_remaining",
                CONF_TARGET: {CONF_ENTITY_ID: "timer.test"},
                CONF_OPTIONS: {"remaining": {"seconds": 30}},
            }
        ],
    )

    # Missing remaining option
    async with expect_raises_async(vol.Invalid):
        await async_validate_trigger_config(
            hass,
            [
                {
                    CONF_PLATFORM: "timer.time_remaining",
                    CONF_TARGET: {CONF_ENTITY_ID: "timer.test"},
                    CONF_OPTIONS: {},
                }
            ],
        )


@test
async def time_remaining_trigger_fires(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test time_remaining trigger fires at the right time."""
    now = dt_util.utcnow()
    calls: list[dict[str, Any]] = []

    hass.states.async_set("timer.test", STATUS_IDLE, {ATTR_LAST_TRANSITION: None})
    await hass.async_block_till_done()

    await _arm_time_remaining_trigger(hass, "timer.test", {"seconds": 30}, calls)

    # Start timer with 60 second duration
    finishes_at = now + timedelta(seconds=60)
    hass.states.async_set(
        "timer.test",
        STATUS_ACTIVE,
        {ATTR_LAST_TRANSITION: "started", ATTR_FINISHES_AT: finishes_at.isoformat()},
    )
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    # Advance to 25 seconds - 35 seconds remaining, should not fire
    freezer.move_to(now + timedelta(seconds=25))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    # Advance to 30 seconds - 30 seconds remaining, should fire
    freezer.move_to(now + timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(calls[0]["entity_id"]).to_equal("timer.test")
    expect(calls[0]["remaining"]).to_equal(timedelta(seconds=30))


@test
async def time_remaining_trigger_paused_before_threshold(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test time_remaining trigger does not fire when timer is paused before threshold."""
    now = dt_util.utcnow()
    calls: list[dict[str, Any]] = []

    hass.states.async_set("timer.test", STATUS_IDLE, {ATTR_LAST_TRANSITION: None})
    await hass.async_block_till_done()

    await _arm_time_remaining_trigger(hass, "timer.test", {"seconds": 30}, calls)

    # Start timer with 60 second duration
    finishes_at = now + timedelta(seconds=60)
    hass.states.async_set(
        "timer.test",
        STATUS_ACTIVE,
        {ATTR_LAST_TRANSITION: "started", ATTR_FINISHES_AT: finishes_at.isoformat()},
    )
    await hass.async_block_till_done()

    # Pause timer at 10 seconds (before the 30-second threshold)
    freezer.move_to(now + timedelta(seconds=10))
    hass.states.async_set(
        "timer.test",
        STATUS_PAUSED,
        {ATTR_LAST_TRANSITION: "paused"},
    )
    await hass.async_block_till_done()

    # Advance past the original fire time - should not fire since paused
    freezer.move_to(now + timedelta(seconds=35))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)


@test
async def time_remaining_trigger_cancelled_before_threshold(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test time_remaining trigger does not fire when timer is cancelled before threshold."""
    now = dt_util.utcnow()
    calls: list[dict[str, Any]] = []

    hass.states.async_set("timer.test", STATUS_IDLE, {ATTR_LAST_TRANSITION: None})
    await hass.async_block_till_done()

    await _arm_time_remaining_trigger(hass, "timer.test", {"seconds": 30}, calls)

    # Start timer with 60 second duration
    finishes_at = now + timedelta(seconds=60)
    hass.states.async_set(
        "timer.test",
        STATUS_ACTIVE,
        {ATTR_LAST_TRANSITION: "started", ATTR_FINISHES_AT: finishes_at.isoformat()},
    )
    await hass.async_block_till_done()

    # Cancel timer at 10 seconds
    freezer.move_to(now + timedelta(seconds=10))
    hass.states.async_set(
        "timer.test",
        STATUS_IDLE,
        {ATTR_LAST_TRANSITION: "cancelled"},
    )
    await hass.async_block_till_done()

    # Advance past the original fire time - should not fire since cancelled
    freezer.move_to(now + timedelta(seconds=35))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)


@test
async def time_remaining_trigger_restarted(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test time_remaining trigger reschedules when timer is restarted."""
    now = dt_util.utcnow()
    calls: list[dict[str, Any]] = []

    hass.states.async_set("timer.test", STATUS_IDLE, {ATTR_LAST_TRANSITION: None})
    await hass.async_block_till_done()

    await _arm_time_remaining_trigger(hass, "timer.test", {"seconds": 30}, calls)

    # Start timer with 60 second duration
    finishes_at = now + timedelta(seconds=60)
    hass.states.async_set(
        "timer.test",
        STATUS_ACTIVE,
        {ATTR_LAST_TRANSITION: "started", ATTR_FINISHES_AT: finishes_at.isoformat()},
    )
    await hass.async_block_till_done()

    # Restart timer at 10 seconds with a new 60-second duration
    freezer.move_to(now + timedelta(seconds=10))
    new_finishes_at = now + timedelta(seconds=70)  # 10s elapsed + 60s new
    hass.states.async_set(
        "timer.test",
        STATUS_ACTIVE,
        {
            ATTR_LAST_TRANSITION: "restarted",
            ATTR_FINISHES_AT: new_finishes_at.isoformat(),
        },
    )
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    # Original fire time (30s) should not fire since rescheduled
    freezer.move_to(now + timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    # New fire time: new_finishes_at - 30s = now + 40s
    freezer.move_to(now + timedelta(seconds=40))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)


@test
async def time_remaining_trigger_short_timer(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test time_remaining trigger does not fire when timer duration is shorter than remaining threshold."""
    now = dt_util.utcnow()
    calls: list[dict[str, Any]] = []

    hass.states.async_set("timer.test", STATUS_IDLE, {ATTR_LAST_TRANSITION: None})
    await hass.async_block_till_done()

    await _arm_time_remaining_trigger(hass, "timer.test", {"seconds": 30}, calls)

    # Start timer with only 20 second duration (less than 30s threshold)
    finishes_at = now + timedelta(seconds=20)
    hass.states.async_set(
        "timer.test",
        STATUS_ACTIVE,
        {ATTR_LAST_TRANSITION: "started", ATTR_FINISHES_AT: finishes_at.isoformat()},
    )
    await hass.async_block_till_done()

    # fire_at = now + 20 - 30 = now - 10 (in the past), should not schedule
    # Advance past the timer's end time
    freezer.move_to(now + timedelta(seconds=25))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)


@test
async def time_remaining_trigger_already_active_at_attach(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test trigger schedules for timers already active when the trigger attaches."""
    now = dt_util.utcnow()
    calls: list[dict[str, Any]] = []

    # Timer is already active before the trigger is armed
    finishes_at = now + timedelta(seconds=60)
    hass.states.async_set(
        "timer.test",
        STATUS_ACTIVE,
        {ATTR_LAST_TRANSITION: "started", ATTR_FINISHES_AT: finishes_at.isoformat()},
    )
    await hass.async_block_till_done()

    await _arm_time_remaining_trigger(hass, "timer.test", {"seconds": 30}, calls)

    # No fire yet
    expect(len(calls)).to_equal(0)

    # Before fire_at (finishes_at - 30s = now + 30s) — should not fire
    freezer.move_to(now + timedelta(seconds=25))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    # At fire_at — should fire even though no state change occurred
    freezer.move_to(now + timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(calls[0]["entity_id"]).to_equal("timer.test")
    expect(calls[0]["remaining"]).to_equal(timedelta(seconds=30))


@test
async def time_remaining_trigger_already_active_past_threshold_at_attach(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test trigger does not schedule for timers already past the fire point at attach."""
    now = dt_util.utcnow()
    calls: list[dict[str, Any]] = []

    # Timer is active but only 20 seconds remain — past the 30s threshold already
    finishes_at = now + timedelta(seconds=20)
    hass.states.async_set(
        "timer.test",
        STATUS_ACTIVE,
        {ATTR_LAST_TRANSITION: "started", ATTR_FINISHES_AT: finishes_at.isoformat()},
    )
    await hass.async_block_till_done()

    await _arm_time_remaining_trigger(hass, "timer.test", {"seconds": 30}, calls)

    # Advance past the timer's finishing time — should never fire
    freezer.move_to(now + timedelta(seconds=25))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)


@test
async def time_remaining_trigger_idle_at_attach(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test trigger does not schedule for non-active timers at attach time."""
    now = dt_util.utcnow()
    calls: list[dict[str, Any]] = []

    hass.states.async_set("timer.test", STATUS_IDLE, {ATTR_LAST_TRANSITION: None})
    await hass.async_block_till_done()

    await _arm_time_remaining_trigger(hass, "timer.test", {"seconds": 30}, calls)

    # Even far in the future, no fire because timer never started
    freezer.move_to(now + timedelta(seconds=120))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)


@test
async def time_remaining_trigger_active_on_first_state_event(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test trigger schedules when first observed state event has no from_state.

    This simulates a timer entity that is created/restored after the trigger
    is attached and appears directly in active state (e.g., RestoreEntity on
    restart), where the initial state-change event has from_state=None.
    """
    now = dt_util.utcnow()
    calls: list[dict[str, Any]] = []

    await _arm_time_remaining_trigger(hass, "timer.test", {"seconds": 30}, calls)

    # First state event for the entity has no old_state
    finishes_at = now + timedelta(seconds=60)
    hass.states.async_set(
        "timer.test",
        STATUS_ACTIVE,
        {ATTR_LAST_TRANSITION: "started", ATTR_FINISHES_AT: finishes_at.isoformat()},
    )
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)

    # Advance to fire time — should still fire even though from_state was None
    freezer.move_to(now + timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(calls[0]["entity_id"]).to_equal("timer.test")
    expect(calls[0]["remaining"]).to_equal(timedelta(seconds=30))


@test
async def time_remaining_trigger_entity_removed_from_target(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test trigger cancels scheduled fire when entity is removed from the target."""
    now = dt_util.utcnow()
    calls: list[dict[str, Any]] = []

    label_reg = lr.async_get(hass)
    label = label_reg.async_create("Test Time Remaining")

    entry = entity_registry.async_get_or_create(
        domain=DOMAIN, platform="test", unique_id="time_remaining_remove"
    )
    entity_registry.async_update_entity(entry.entity_id, labels={label.label_id})

    hass.states.async_set(entry.entity_id, STATUS_IDLE, {ATTR_LAST_TRANSITION: None})
    await hass.async_block_till_done()

    await _arm_time_remaining_trigger(
        hass,
        entry.entity_id,
        {"seconds": 30},
        calls,
        target={ATTR_LABEL_ID: label.label_id},
    )

    # Start the timer — this schedules a fire via the state-change path
    finishes_at = now + timedelta(seconds=60)
    hass.states.async_set(
        entry.entity_id,
        STATUS_ACTIVE,
        {ATTR_LAST_TRANSITION: "started", ATTR_FINISHES_AT: finishes_at.isoformat()},
    )
    await hass.async_block_till_done()

    # Remove the entity from the target by stripping its label
    freezer.move_to(now + timedelta(seconds=10))
    entity_registry.async_update_entity(entry.entity_id, labels=set())
    await hass.async_block_till_done()

    # Advance past the original fire time — should not fire since cancelled
    freezer.move_to(now + timedelta(seconds=35))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(0)


@test
async def time_remaining_trigger_entity_added_to_target(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _labs: None = Depends(enable_labs_preview_features),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test trigger schedules a fire for an active timer added to the target later."""
    now = dt_util.utcnow()
    calls: list[dict[str, Any]] = []

    label_reg = lr.async_get(hass)
    label = label_reg.async_create("Test Time Remaining Add")

    entry = entity_registry.async_get_or_create(
        domain=DOMAIN, platform="test", unique_id="time_remaining_add"
    )

    # Timer is active, but not in the target yet
    finishes_at = now + timedelta(seconds=60)
    hass.states.async_set(
        entry.entity_id,
        STATUS_ACTIVE,
        {ATTR_LAST_TRANSITION: "started", ATTR_FINISHES_AT: finishes_at.isoformat()},
    )
    await hass.async_block_till_done()

    await _arm_time_remaining_trigger(
        hass,
        entry.entity_id,
        {"seconds": 30},
        calls,
        target={ATTR_LABEL_ID: label.label_id},
    )

    # Now label the entity so it joins the target
    entity_registry.async_update_entity(entry.entity_id, labels={label.label_id})
    await hass.async_block_till_done()

    # Advance to the fire time — should fire even though no state change occurred
    freezer.move_to(now + timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(calls[0]["entity_id"]).to_equal(entry.entity_id)
    expect(calls[0]["remaining"]).to_equal(timedelta(seconds=30))
