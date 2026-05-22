"""The tests the History component."""

from copy import copy
from datetime import datetime, timedelta
import json
from typing import Any

from freezegun import freeze_time
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
from homeassistant.helpers.json import JSONEncoder
from homeassistant.util import dt as dt_util

from tests.hass_fixtures import hass as hass_fixture

from ._fixtures import recorder_mock
from .common import (
    assert_dict_of_states_equal_without_context,
    assert_dict_of_states_equal_without_context_and_last_changed,
    assert_multiple_states_equal_without_context,
    assert_multiple_states_equal_without_context_and_last_changed,
    assert_states_equal_without_context,
    async_wait_recording_done,
    db_state_attributes_to_native,
    db_state_to_native,
    record_states,
    wait_recording_done,
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


def _add_db_entries(
    hass: HomeAssistant, point: datetime, entity_ids: list[str]
) -> None:
    """Add a few states to the database for testing."""
    with recorder.util.session_scope(hass=hass) as session:
        for idx, entity_id in enumerate(entity_ids):
            session.add(
                States(
                    entity_id=entity_id,
                    state=f"-{idx}",
                    last_changed_ts=(point - timedelta(minutes=idx)).timestamp(),
                    last_updated_ts=(point - timedelta(minutes=idx)).timestamp(),
                )
            )


@test
async def state_changes_during_period(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test state changes during period."""
    entity_id = "media_player.test"

    def set_state(state: str) -> State:
        """Set the state."""
        hass.states.async_set(entity_id, state)
        wait_recording_done(hass)
        return hass.states.get(entity_id)

    start = dt_util.utcnow()
    point = start + timedelta(seconds=1)
    end = point + timedelta(seconds=1)

    with freeze_time(start) as freezer:
        set_state("idle")
        set_state("YouTube")

        freezer.move_to(point)
        states = [
            set_state("idle"),
            set_state("Netflix"),
            set_state("Plex"),
        ]

        freezer.move_to(end)
        set_state("Netflix")
        set_state("Plex")

    hist = history.state_changes_during_period(hass, start, end, entity_id)

    assert_multiple_states_equal_without_context(states, hist[entity_id])


@test
async def state_changes_during_period_last_reported(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test state changes during period laste reported."""
    entity_id = "media_player.test"

    def set_state(state: str) -> State:
        """Set the state."""
        hass.states.async_set(entity_id, state)
        wait_recording_done(hass)
        return hass.states.get(entity_id)

    start = dt_util.utcnow()
    point1 = start + timedelta(seconds=1)
    point2 = point1 + timedelta(seconds=1)
    end = point2 + timedelta(seconds=1)

    with freeze_time(start) as freezer:
        set_state("idle")

        freezer.move_to(point1)
        states = [set_state("YouTube")]

        freezer.move_to(point2)
        set_state("YouTube")

        freezer.move_to(end)
        set_state("Netflix")

    hist = history.state_changes_during_period(hass, start, end, entity_id)

    assert_multiple_states_equal_without_context_and_last_changed(
        states, hist[entity_id]
    )


@test
async def state_changes_during_period_descending(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test state changes during period descending."""
    entity_id = "media_player.test"

    def set_state(state: str) -> State:
        """Set the state."""
        hass.states.async_set(entity_id, state)
        wait_recording_done(hass)
        return hass.states.get(entity_id)

    start = dt_util.utcnow().replace(microsecond=0)
    point = start + timedelta(seconds=1)
    point2 = start + timedelta(seconds=1, microseconds=100)
    point3 = start + timedelta(seconds=1, microseconds=200)
    point4 = start + timedelta(seconds=1, microseconds=300)
    end = point + timedelta(seconds=1, microseconds=400)

    with freeze_time(start) as freezer:
        set_state("idle")
        set_state("YouTube")

        freezer.move_to(point)
        states = [set_state("idle")]

        freezer.move_to(point2)
        states.append(set_state("Netflix"))

        freezer.move_to(point3)
        states.append(set_state("Plex"))

        freezer.move_to(point4)
        states.append(set_state("YouTube"))

        freezer.move_to(end)
        set_state("Netflix")
        set_state("Plex")

    hist = history.state_changes_during_period(
        hass, start, end, entity_id, no_attributes=True, descending=False
    )
    assert_multiple_states_equal_without_context_and_last_changed(
        states, hist[entity_id]
    )

    hist = history.state_changes_during_period(
        hass, start, end, entity_id, no_attributes=True, descending=True
    )
    assert_multiple_states_equal_without_context_and_last_changed(
        states, list(reversed(list(hist[entity_id])))
    )

    start_time = point2 + timedelta(microseconds=10)
    hist = history.state_changes_during_period(
        hass,
        start_time,  # Pick a point where we will generate a start time state
        end,
        entity_id,
        no_attributes=True,
        descending=True,
        include_start_time_state=True,
    )
    hist_states = list(hist[entity_id])
    expect(hist_states[-1].last_updated).to_equal(start_time)
    expect(hist_states[-1].last_changed).to_equal(start_time)
    expect(len(hist_states)).to_equal(3)


@test
async def get_last_state_changes(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test number of state changes."""
    entity_id = "sensor.test"

    def set_state(state: str) -> State:
        """Set the state."""
        hass.states.async_set(entity_id, state)
        wait_recording_done(hass)
        return hass.states.get(entity_id)

    start = dt_util.utcnow() - timedelta(minutes=2)
    point = start + timedelta(minutes=1)
    point2 = point + timedelta(minutes=1, seconds=1)
    states = []

    with freeze_time(start) as freezer:
        set_state("1")

        freezer.move_to(point)
        states.append(set_state("2"))

        freezer.move_to(point2)
        states.append(set_state("3"))

    hist = history.get_last_state_changes(hass, 2, entity_id)

    assert_multiple_states_equal_without_context(states, hist[entity_id])


@test
async def get_last_state_changes_last_reported(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test number of state changes."""
    entity_id = "sensor.test"

    def set_state(state: str) -> State:
        """Set the state."""
        hass.states.async_set(entity_id, state)
        wait_recording_done(hass)
        return hass.states.get(entity_id)

    start = dt_util.utcnow() - timedelta(minutes=2)
    point = start + timedelta(minutes=1)
    point2 = point + timedelta(minutes=1, seconds=1)
    states = []

    with freeze_time(start) as freezer:
        states.append(set_state("1"))

        freezer.move_to(point)
        set_state("1")

        freezer.move_to(point2)
        states.append(set_state("2"))

    hist = history.get_last_state_changes(hass, 2, entity_id)

    assert_multiple_states_equal_without_context_and_last_changed(
        states, hist[entity_id]
    )


@test
async def get_last_state_change(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test getting the last state change for an entity."""
    entity_id = "sensor.test"

    def set_state(state: str) -> State:
        """Set the state."""
        hass.states.async_set(entity_id, state)
        wait_recording_done(hass)
        return hass.states.get(entity_id)

    start = dt_util.utcnow() - timedelta(minutes=2)
    point = start + timedelta(minutes=1)
    point2 = point + timedelta(minutes=1, seconds=1)
    states = []

    with freeze_time(start) as freezer:
        set_state("1")

        freezer.move_to(point)
        set_state("2")

        freezer.move_to(point2)
        states.append(set_state("3"))

    hist = history.get_last_state_changes(hass, 1, entity_id)

    assert_multiple_states_equal_without_context(states, hist[entity_id])


@test
async def ensure_state_can_be_copied(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Ensure a state can be copied during migration and not have impacted state."""
    entity_id = "sensor.test"

    def set_state(state: str) -> State:
        """Set the state."""
        hass.states.async_set(entity_id, state)
        wait_recording_done(hass)
        return hass.states.get(entity_id)

    start = dt_util.utcnow() - timedelta(minutes=2)
    point = start + timedelta(minutes=1)

    with freeze_time(start) as freezer:
        set_state("1")

        freezer.move_to(point)
        set_state("2")

    hist = history.get_last_state_changes(hass, 2, entity_id)

    assert_states_equal_without_context(
        copy(hist[entity_id][0]), hist[entity_id][0]
    )
    assert_states_equal_without_context(
        copy(hist[entity_id][1]), hist[entity_id][1]
    )


@test
async def get_significant_states(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that only significant states are returned.

    We should get back every thermostat change that
    includes an attribute change, but only the state updates for
    media player (attribute changes are not significant and not returned).
    """
    zero, four, states = record_states(hass)
    hist = history.get_significant_states(
        hass, zero, four, entity_ids=list(states)
    )
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)


@test
async def get_significant_states_minimal_response(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that only significant states are returned.

    When minimal responses is set only the first and
    last states return a complete state.
    """
    zero, four, states = record_states(hass)
    hist = history.get_significant_states(
        hass, zero, four, minimal_response=True, entity_ids=list(states)
    )
    entites_with_reducable_states = [
        "media_player.test",
        "media_player.test3",
    ]

    # All states for media_player.test state are reduced
    # down to last_changed and state when minimal_response
    # is set except for the first state.
    #
    # is_initial = state.last_changed == state.last_updated
    media_player_test_states = states["media_player.test"]
    assert len(media_player_test_states) == 2

    # Make sure we don't return a reduced response for the first state
    assert isinstance(hist["media_player.test"][0], State)

    # Make sure we do return a reduced response for the rest of the states
    assert isinstance(hist["media_player.test"][1], dict)

    for entity_id in entites_with_reducable_states:
        entity_states = states[entity_id]
        for state_idx in range(1, len(entity_states)):
            input_state = entity_states[state_idx]
            orig_last_changed = orig_last_changed = json.dumps(
                process_timestamp(input_state.last_changed),
                cls=JSONEncoder,
            ).replace('"', "")
            orig_state = input_state.state
            entity_states[state_idx] = {
                "last_changed": orig_last_changed,
                "state": orig_state,
            }

    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)


@test
async def get_significant_states_with_initial(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that only significant states are returned.

    We should get back every thermostat change that
    includes an attribute change, but only the state updates for
    media player (attribute changes are not significant and not returned).
    """
    zero, four, states = record_states(hass)
    one_and_half = zero + timedelta(seconds=1 * 5) + timedelta(seconds=15 * 5 / 2)
    for entity_id in states:
        if entity_id == "media_player.test":
            states[entity_id] = states[entity_id][1:]
        for state in states[entity_id]:
            # If the state is recorded before the start time
            # start it will have its last_updated and last_changed
            # set to the start time.
            if state.last_updated < one_and_half:
                state.last_updated = one_and_half
                state.last_changed = one_and_half

    hist = history.get_significant_states(
        hass,
        one_and_half,
        four,
        include_start_time_state=True,
        entity_ids=list(states),
    )
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)


@test
async def get_significant_states_without_initial(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that only significant states are returned.

    We should get back every thermostat change that
    includes an attribute change, but only the state updates for
    media player (attribute changes are not significant and not returned).
    """
    zero, four, states = record_states(hass)
    one = zero + timedelta(seconds=1 * 5)
    one_with_microsecond = one + timedelta(microseconds=1)
    one_and_half = zero + timedelta(seconds=1 * 5) + timedelta(seconds=15 * 5 / 2)
    for entity_id in states:
        states[entity_id] = list(
            filter(
                lambda s: s.last_changed not in (one, one_with_microsecond),
                states[entity_id],
            )
        )
    del states["media_player.test2"]
    del states["media_player.test3"]

    hist = history.get_significant_states(
        hass,
        one_and_half,
        four,
        include_start_time_state=False,
        entity_ids=list(states),
    )
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)


@test
async def get_significant_states_entity_id(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that only significant states are returned for one entity."""
    zero, four, states = record_states(hass)
    del states["media_player.test2"]
    del states["media_player.test3"]
    del states["thermostat.test"]
    del states["thermostat.test2"]
    del states["script.can_cancel_this_one"]

    hist = history.get_significant_states(
        hass, zero, four, ["media_player.test"]
    )
    assert_dict_of_states_equal_without_context_and_last_changed(states, hist)


@test
async def get_significant_states_multiple_entity_ids(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that only significant states are returned for one entity."""
    zero, four, states = record_states(hass)

    hist = history.get_significant_states(
        hass,
        zero,
        four,
        ["media_player.test", "thermostat.test"],
    )

    assert_multiple_states_equal_without_context_and_last_changed(
        states["media_player.test"], hist["media_player.test"]
    )
    assert_multiple_states_equal_without_context_and_last_changed(
        states["thermostat.test"], hist["thermostat.test"]
    )


@test
async def get_significant_states_are_ordered(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test order of results from get_significant_states.

    When entity ids are given, the results should be returned with the data
    in the same order.
    """
    zero, four, _states = record_states(hass)
    entity_ids = ["media_player.test", "media_player.test2"]
    hist = history.get_significant_states(hass, zero, four, entity_ids)
    assert list(hist.keys()) == entity_ids
    entity_ids = ["media_player.test2", "media_player.test"]
    hist = history.get_significant_states(hass, zero, four, entity_ids)
    assert list(hist.keys()) == entity_ids


@test
async def get_significant_states_only(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test significant states when significant_states_only is set."""
    entity_id = "sensor.test"

    def set_state(state: str, **kwargs: Any) -> State:
        """Set the state."""
        hass.states.async_set(entity_id, state, **kwargs)
        wait_recording_done(hass)
        return hass.states.get(entity_id)

    start = dt_util.utcnow() - timedelta(minutes=4)
    points = [start + timedelta(minutes=i) for i in range(1, 4)]

    states = []
    with freeze_time(start) as freezer:
        set_state("123", attributes={"attribute": 10.64})

        freezer.move_to(points[0])
        # Attributes are different, state not
        states.append(set_state("123", attributes={"attribute": 21.42}))

        freezer.move_to(points[1])
        # state is different, attributes not
        states.append(set_state("32", attributes={"attribute": 21.42}))

        freezer.move_to(points[2])
        # everything is different
        states.append(set_state("412", attributes={"attribute": 54.23}))

    hist = history.get_significant_states(
        hass,
        start,
        significant_changes_only=True,
        entity_ids=list({state.entity_id for state in states}),
    )

    assert len(hist[entity_id]) == 2
    assert not any(
        state.last_updated == states[0].last_updated for state in hist[entity_id]
    )
    assert any(
        state.last_updated == states[1].last_updated for state in hist[entity_id]
    )
    assert any(
        state.last_updated == states[2].last_updated for state in hist[entity_id]
    )

    hist = history.get_significant_states(
        hass,
        start,
        significant_changes_only=False,
        entity_ids=list({state.entity_id for state in states}),
    )

    assert len(hist[entity_id]) == 3
    assert_multiple_states_equal_without_context_and_last_changed(
        states, hist[entity_id]
    )


@test
async def get_significant_states_only_minimal_response(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test significant states when significant_states_only is True."""
    now = dt_util.utcnow()
    _add_db_entries(
        hass,
        now,
        [
            "sensor.one",
            "sensor.two",
            "sensor.three",
        ],
    )
    await async_wait_recording_done(hass)

    hist = history.get_significant_states(
        hass,
        now - timedelta(minutes=5),
        entity_ids=["sensor.one", "sensor.two", "sensor.three"],
        significant_changes_only=True,
        minimal_response=True,
    )
    assert len(hist) == 3
    assert "sensor.one" in hist
    assert "sensor.two" in hist
    assert "sensor.three" in hist


@test
async def get_full_significant_states_past_year_2038(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we can store times past year 2038."""
    past_2038_time = dt_util.parse_datetime("2039-01-19 03:14:07.555555-00:00")
    hass.states.async_set("sensor.one", "on", {"attr": "original"})
    state0 = hass.states.get("sensor.one")
    await hass.async_block_till_done()

    with freeze_time(past_2038_time):
        hass.states.async_set("sensor.one", "on", {"attr": "new"})
        state1 = hass.states.get("sensor.one")

    await async_wait_recording_done(hass)

    def _get_entries():
        with session_scope(hass=hass, read_only=True) as session:
            return history.get_full_significant_states_with_session(
                hass,
                session,
                past_2038_time - timedelta(days=365),
                past_2038_time + timedelta(days=365),
                entity_ids=["sensor.one"],
                significant_changes_only=False,
            )

    states = await recorder.get_instance(hass).async_add_executor_job(_get_entries)
    sensor_one_states: list[State] = states["sensor.one"]
    assert_states_equal_without_context(sensor_one_states[0], state0)
    assert_states_equal_without_context(sensor_one_states[1], state1)
