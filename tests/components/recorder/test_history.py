"""The tests the History component."""

from datetime import timedelta
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import recorder
from homeassistant.components.recorder import history
from homeassistant.components.recorder.db_schema import (
    StateAttributes,
    States,
    StatesMeta,
)
from homeassistant.components.recorder.filters import Filters
from homeassistant.components.recorder.models import process_timestamp
from homeassistant.components.recorder.util import session_scope
from homeassistant.core import HomeAssistant, State
from homeassistant.util import dt as dt_util

from tests.hass_fixtures import hass as hass_fixture

from ._fixtures import recorder_mock
from .common import (
    assert_states_equal_without_context,
    async_wait_recording_done,
    db_state_attributes_to_native,
    db_state_to_native,
)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _recorder: Any = Depends(recorder_mock),
) -> HomeAssistant:
    """Opt the module into Tryke's HookExecutor path with recorder set up."""
    return hass


@test
async def get_full_significant_states_with_session_entity_no_matches(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test getting states at a specific point in time for entities that never have been recorded."""
    now = dt_util.utcnow()
    time_before_recorder_ran = now - timedelta(days=1000)
    with session_scope(hass=hass, read_only=True) as session:
        expect(
            history.get_full_significant_states_with_session(
                hass, session, time_before_recorder_ran, now, entity_ids=["demo.id"]
            )
        ).to_equal({})
        expect(
            history.get_full_significant_states_with_session(
                hass,
                session,
                time_before_recorder_ran,
                now,
                entity_ids=["demo.id", "demo.id2"],
            )
        ).to_equal({})


@test
async def significant_states_with_session_entity_minimal_response_no_matches(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test getting states at a specific point in time for entities that never have been recorded."""
    now = dt_util.utcnow()
    time_before_recorder_ran = now - timedelta(days=1000)
    with session_scope(hass=hass, read_only=True) as session:
        expect(
            history.get_significant_states_with_session(
                hass,
                session,
                time_before_recorder_ran,
                now,
                entity_ids=["demo.id"],
                minimal_response=True,
            )
        ).to_equal({})
        expect(
            history.get_significant_states_with_session(
                hass,
                session,
                time_before_recorder_ran,
                now,
                entity_ids=["demo.id", "demo.id2"],
                minimal_response=True,
            )
        ).to_equal({})


@test
async def significant_states_with_session_single_entity(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test get_significant_states_with_session with a single entity."""
    hass.states.async_set("demo.id", "any", {"attr": True})
    hass.states.async_set("demo.id", "any2", {"attr": True})
    await async_wait_recording_done(hass)
    now = dt_util.utcnow()
    with session_scope(hass=hass, read_only=True) as session:
        states = history.get_significant_states_with_session(
            hass,
            session,
            now - timedelta(days=1),
            now,
            entity_ids=["demo.id"],
            minimal_response=False,
        )
        expect(len(states["demo.id"])).to_equal(2)


@test
async def get_full_significant_states_handles_empty_last_changed(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test getting states when last_changed is null."""
    now = dt_util.utcnow()
    hass.states.async_set("sensor.one", "on", {"attr": "original"})
    state0 = hass.states.get("sensor.one")
    await hass.async_block_till_done()
    hass.states.async_set("sensor.one", "on", {"attr": "new"})
    state1 = hass.states.get("sensor.one")

    expect(state0.last_changed).to_equal(state1.last_changed)
    expect(state0.last_updated != state1.last_updated).to_be(True)
    await async_wait_recording_done(hass)

    def _get_entries():
        with session_scope(hass=hass, read_only=True) as session:
            return history.get_full_significant_states_with_session(
                hass,
                session,
                now,
                dt_util.utcnow(),
                entity_ids=["sensor.one"],
                significant_changes_only=False,
            )

    states = await recorder.get_instance(hass).async_add_executor_job(_get_entries)
    sensor_one_states: list[State] = states["sensor.one"]
    assert_states_equal_without_context(sensor_one_states[0], state0)
    assert_states_equal_without_context(sensor_one_states[1], state1)
    expect(sensor_one_states[0].last_changed).to_equal(sensor_one_states[1].last_changed)
    expect(sensor_one_states[0].last_updated != sensor_one_states[1].last_updated).to_be(
        True
    )

    def _fetch_native_states() -> list[State]:
        with session_scope(hass=hass, read_only=True) as session:
            native_states = []
            db_state_attributes = {
                state_attributes.attributes_id: state_attributes
                for state_attributes in session.query(StateAttributes)
            }
            metadata_id_to_entity_id = {
                states_meta.metadata_id: states_meta
                for states_meta in session.query(StatesMeta)
            }
            for db_state in session.query(States):
                db_state.entity_id = metadata_id_to_entity_id[
                    db_state.metadata_id
                ].entity_id
                state = db_state_to_native(db_state)
                state.attributes = db_state_attributes_to_native(
                    db_state_attributes[db_state.attributes_id]
                )
                native_states.append(state)
            return native_states

    native_sensor_one_states = await recorder.get_instance(
        hass
    ).async_add_executor_job(_fetch_native_states)
    assert_states_equal_without_context(native_sensor_one_states[0], state0)
    assert_states_equal_without_context(native_sensor_one_states[1], state1)
    expect(native_sensor_one_states[0].last_changed).to_equal(
        native_sensor_one_states[1].last_changed
    )
    expect(
        native_sensor_one_states[0].last_updated
        != native_sensor_one_states[1].last_updated
    ).to_be(True)

    def _fetch_db_states() -> list[States]:
        with session_scope(hass=hass, read_only=True) as session:
            states = list(session.query(States))
            session.expunge_all()
            return states

    db_sensor_one_states = await recorder.get_instance(hass).async_add_executor_job(
        _fetch_db_states
    )
    expect(db_sensor_one_states[0].last_changed).to_be_none()
    expect(db_sensor_one_states[0].last_changed_ts).to_be_none()

    expect(
        process_timestamp(
            dt_util.utc_from_timestamp(db_sensor_one_states[1].last_changed_ts)
        )
    ).to_equal(state0.last_changed)
    expect(db_sensor_one_states[0].last_updated_ts is not None).to_be(True)
    expect(db_sensor_one_states[1].last_updated_ts is not None).to_be(True)
    expect(
        db_sensor_one_states[0].last_updated_ts
        != db_sensor_one_states[1].last_updated_ts
    ).to_be(True)


@test
async def state_changes_during_period_multiple_entities_single_test(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test state change during period with multiple entities in the same test.

    This test ensures the sqlalchemy query cache does not
    generate incorrect results.
    """
    start = dt_util.utcnow()
    test_entites = {f"sensor.{i}": str(i) for i in range(30)}
    for entity_id, value in test_entites.items():
        hass.states.async_set(entity_id, value)
    await async_wait_recording_done(hass)

    end = dt_util.utcnow()

    for entity_id, value in test_entites.items():
        hist = history.state_changes_during_period(hass, start, end, entity_id)
        expect(len(hist)).to_equal(1)
        expect(hist[entity_id][0].state).to_equal(value)


@test
async def get_significant_states_without_entity_ids_raises(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test at least one entity id is required for get_significant_states."""
    now = dt_util.utcnow()
    expect(lambda: history.get_significant_states(hass, now, None)).to_raise(
        ValueError, match="entity_ids must be provided"
    )


@test
async def state_changes_during_period_without_entity_ids_raises(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test at least one entity id is required for state_changes_during_period."""
    now = dt_util.utcnow()
    expect(lambda: history.state_changes_during_period(hass, now, None)).to_raise(
        ValueError, match="entity_id must be provided"
    )


@test
async def get_significant_states_with_filters_raises(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test passing filters is no longer supported."""
    now = dt_util.utcnow()
    expect(
        lambda: history.get_significant_states(
            hass, now, None, ["media_player.test"], Filters()
        )
    ).to_raise(NotImplementedError, match="Filters are no longer supported")


@test
async def get_significant_states_with_non_existent_entity_ids_returns_empty(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test get_significant_states returns an empty dict when entities not in the db."""
    now = dt_util.utcnow()
    expect(
        history.get_significant_states(hass, now, None, ["nonexistent.entity"])
    ).to_equal({})


@test
async def state_changes_during_period_with_non_existent_entity_ids_returns_empty(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test state_changes_during_period returns an empty dict when entities not in the db."""
    now = dt_util.utcnow()
    expect(
        history.state_changes_during_period(hass, now, None, "nonexistent.entity")
    ).to_equal({})


@test
async def get_last_state_changes_with_non_existent_entity_ids_returns_empty(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test get_last_state_changes returns an empty dict when entities not in the db."""
    expect(history.get_last_state_changes(hass, 1, "nonexistent.entity")).to_equal({})


# Tests still using freeze_time / parametrize / record_states helper remain
# deferred until those facilities are ported into the tryke shim.


@test.skip("uses freeze_time/parametrize (port deferred)")
async def state_changes_during_period() -> None:
    """Stub for test_state_changes_during_period (port deferred)."""


@test.skip("uses freeze_time (port deferred)")
async def state_changes_during_period_last_reported() -> None:
    """Stub for test_state_changes_during_period_last_reported (port deferred)."""


@test.skip("uses freeze_time (port deferred)")
async def state_changes_during_period_descending() -> None:
    """Stub for test_state_changes_during_period_descending (port deferred)."""


@test.skip("uses freeze_time (port deferred)")
async def get_last_state_changes() -> None:
    """Stub for test_get_last_state_changes (port deferred)."""


@test.skip("uses freeze_time (port deferred)")
async def get_last_state_changes_last_reported() -> None:
    """Stub for test_get_last_state_changes_last_reported (port deferred)."""


@test.skip("uses freeze_time (port deferred)")
async def get_last_state_change() -> None:
    """Stub for test_get_last_state_change (port deferred)."""


@test.skip("uses freeze_time (port deferred)")
async def ensure_state_can_be_copied() -> None:
    """Stub for test_ensure_state_can_be_copied (port deferred)."""


@test.skip("uses record_states helper / freeze_time (port deferred)")
async def get_significant_states() -> None:
    """Stub for test_get_significant_states (port deferred)."""


@test.skip("uses record_states helper / freeze_time (port deferred)")
async def get_significant_states_minimal_response() -> None:
    """Stub for test_get_significant_states_minimal_response (port deferred)."""


@test.skip("uses record_states helper / parametrize / freeze_time (port deferred)")
async def get_significant_states_with_initial() -> None:
    """Stub for test_get_significant_states_with_initial (port deferred)."""


@test.skip("uses record_states helper / freeze_time (port deferred)")
async def get_significant_states_without_initial() -> None:
    """Stub for test_get_significant_states_without_initial (port deferred)."""


@test.skip("uses record_states helper / freeze_time (port deferred)")
async def get_significant_states_entity_id() -> None:
    """Stub for test_get_significant_states_entity_id (port deferred)."""


@test.skip("uses record_states helper / freeze_time (port deferred)")
async def get_significant_states_multiple_entity_ids() -> None:
    """Stub for test_get_significant_states_multiple_entity_ids (port deferred)."""


@test.skip("uses record_states helper / freeze_time (port deferred)")
async def get_significant_states_are_ordered() -> None:
    """Stub for test_get_significant_states_are_ordered (port deferred)."""


@test.skip("uses record_states helper / freeze_time (port deferred)")
async def get_significant_states_only() -> None:
    """Stub for test_get_significant_states_only (port deferred)."""


@test.skip("uses record_states helper / freeze_time (port deferred)")
async def get_significant_states_only_minimal_response() -> None:
    """Stub for test_get_significant_states_only_minimal_response (port deferred)."""


@test.skip("uses pytest.mark.freeze_time (port deferred)")
async def get_full_significant_states_past_year_2038() -> None:
    """Stub for test_get_full_significant_states_past_year_2038 (port deferred)."""
