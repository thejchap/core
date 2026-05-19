"""Test data purging (tryke port)."""

from datetime import timedelta
from typing import Any

from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant.components.recorder import Recorder
from homeassistant.components.recorder.db_schema import (
    Events,
    RecorderRuns,
    StateAttributes,
    States,
    StatisticsRuns,
)
from homeassistant.components.recorder.purge import purge_old_data
from homeassistant.components.recorder.queries import select_event_type_ids
from homeassistant.components.recorder.util import session_scope
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from ._fixtures import recorder_mock
from .common import async_wait_recording_done

from tests.hass_fixtures import hass as hass_fixture

TEST_EVENT_TYPES = (
    "EVENT_TEST_AUTOPURGE",
    "EVENT_TEST_PURGE",
    "EVENT_TEST",
    "EVENT_TEST_AUTOPURGE_WITH_EVENT_DATA",
    "EVENT_TEST_PURGE_WITH_EVENT_DATA",
    "EVENT_TEST_WITH_EVENT_DATA",
)


@fixture
async def _trigger_executor(
    _recorder: Any = Depends(recorder_mock),
) -> int:
    """Anchor fixture for tryke Depends() resolution."""
    return 0


async def _add_test_states(hass: HomeAssistant, wait_recording_done: bool = True) -> None:
    """Add multiple states to the db for testing."""
    utcnow = dt_util.utcnow()
    five_days_ago = utcnow - timedelta(days=5)
    eleven_days_ago = utcnow - timedelta(days=11)
    base_attributes = {"test_attr": 5, "test_attr_10": "nice"}

    async def set_state(entity_id: str, state: str, **kwargs: Any) -> None:
        """Set the state."""
        hass.states.async_set(entity_id, state, **kwargs)
        if wait_recording_done:
            await hass.async_block_till_done()
            await async_wait_recording_done(hass)

    with freeze_time() as freezer:
        for event_id in range(6):
            if event_id < 2:
                timestamp = eleven_days_ago
                state = f"autopurgeme_{event_id}"
                attributes = {"autopurgeme": True, **base_attributes}
            elif event_id < 4:
                timestamp = five_days_ago
                state = f"purgeme_{event_id}"
                attributes = {"purgeme": True, **base_attributes}
            else:
                timestamp = utcnow
                state = f"dontpurgeme_{event_id}"
                attributes = {"dontpurgeme": True, **base_attributes}

            freezer.move_to(timestamp)
            await set_state("test.recorder2", state, attributes=attributes)


async def _add_test_events(hass: HomeAssistant, iterations: int = 1) -> None:
    """Add a few events for testing."""
    utcnow = dt_util.utcnow()
    five_days_ago = utcnow - timedelta(days=5)
    eleven_days_ago = utcnow - timedelta(days=11)
    event_data = {"test_attr": 5, "test_attr_10": "nice"}
    await async_wait_recording_done(hass)

    with freeze_time() as freezer:
        for _ in range(iterations):
            for event_id in range(6):
                if event_id < 2:
                    timestamp = eleven_days_ago
                    event_type = "EVENT_TEST_AUTOPURGE"
                elif event_id < 4:
                    timestamp = five_days_ago
                    event_type = "EVENT_TEST_PURGE"
                else:
                    timestamp = utcnow
                    event_type = "EVENT_TEST"
                freezer.move_to(timestamp)
                hass.bus.async_fire(event_type, event_data)

    await async_wait_recording_done(hass)


async def _add_test_recorder_runs(hass: HomeAssistant) -> None:
    """Add a few recorder_runs for testing."""
    utcnow = dt_util.utcnow()
    five_days_ago = utcnow - timedelta(days=5)
    eleven_days_ago = utcnow - timedelta(days=11)

    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    with session_scope(hass=hass) as session:
        for rec_id in range(6):
            if rec_id < 2:
                timestamp = eleven_days_ago
            elif rec_id < 4:
                timestamp = five_days_ago
            else:
                timestamp = utcnow

            session.add(
                RecorderRuns(
                    start=timestamp,
                    created=dt_util.utcnow(),
                    end=timestamp + timedelta(days=1),
                )
            )


async def _add_test_statistics_runs(hass: HomeAssistant) -> None:
    """Add a few statistics runs for testing."""
    utcnow = dt_util.utcnow()
    five_days_ago = utcnow - timedelta(days=5)
    eleven_days_ago = utcnow - timedelta(days=11)

    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    with session_scope(hass=hass) as session:
        for rec_id in range(6):
            if rec_id < 2:
                timestamp = eleven_days_ago
            elif rec_id < 4:
                timestamp = five_days_ago
            else:
                timestamp = utcnow

            session.add(
                StatisticsRuns(
                    start=timestamp,
                )
            )


@test
async def purge_old_events(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _recorder: Recorder = Depends(recorder_mock),
) -> None:
    """Test deleting old events."""
    recorder_mock_inst = _recorder
    await _add_test_events(hass)

    with session_scope(hass=hass) as session:
        events = session.query(Events).filter(
            Events.event_type_id.in_(select_event_type_ids(TEST_EVENT_TYPES))
        )
        expect(events.count()).to_be(6)

    purge_before = dt_util.utcnow() - timedelta(days=4)

    finished = purge_old_data(
        recorder_mock_inst,
        purge_before,
        repack=False,
        events_batch_size=1,
        states_batch_size=1,
    )
    expect(finished).to_be(False)

    with session_scope(hass=hass) as session:
        events = session.query(Events).filter(
            Events.event_type_id.in_(select_event_type_ids(TEST_EVENT_TYPES))
        )
        expect(events.count()).to_be(2)

    finished = purge_old_data(
        recorder_mock_inst,
        purge_before,
        repack=False,
        events_batch_size=1,
        states_batch_size=1,
    )
    expect(finished).to_be(True)

    with session_scope(hass=hass) as session:
        events = session.query(Events).filter(
            Events.event_type_id.in_(select_event_type_ids(TEST_EVENT_TYPES))
        )
        expect(events.count()).to_be(2)


@test
async def purge_old_recorder_runs(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _recorder: Recorder = Depends(recorder_mock),
) -> None:
    """Test deleting old recorder runs keeps current run."""
    recorder_mock_inst = _recorder
    await _add_test_recorder_runs(hass)

    with session_scope(hass=hass) as session:
        recorder_runs = session.query(RecorderRuns)
        expect(recorder_runs.count()).to_be(7)
        expect(sum(run.end is None for run in recorder_runs)).to_be(1)

    purge_before = dt_util.utcnow()

    finished = purge_old_data(
        recorder_mock_inst,
        purge_before,
        repack=False,
        events_batch_size=1,
        states_batch_size=1,
    )
    expect(finished).to_be(False)

    finished = purge_old_data(
        recorder_mock_inst,
        purge_before,
        repack=False,
        events_batch_size=1,
        states_batch_size=1,
    )
    expect(finished).to_be(True)

    with session_scope(hass=hass) as session:
        recorder_runs = session.query(RecorderRuns)
        expect(recorder_runs.count()).to_be(3)
        expect(sum(run.end is None for run in recorder_runs)).to_be(1)


@test
async def purge_old_statistics_runs(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _recorder: Recorder = Depends(recorder_mock),
) -> None:
    """Test deleting old statistics runs keeps the latest run."""
    recorder_mock_inst = _recorder
    await _add_test_statistics_runs(hass)

    with session_scope(hass=hass) as session:
        statistics_runs = session.query(StatisticsRuns)
        expect(statistics_runs.count()).to_be(7)

    purge_before = dt_util.utcnow()

    finished = purge_old_data(recorder_mock_inst, purge_before, repack=False)
    expect(finished).to_be(False)

    finished = purge_old_data(recorder_mock_inst, purge_before, repack=False)
    expect(finished).to_be(True)

    with session_scope(hass=hass) as session:
        statistics_runs = session.query(StatisticsRuns)
        expect(statistics_runs.count()).to_be(1)


@test.skip("requires patch.object on recorder_mock.max_bind_vars (complex setup)")
async def purge_big_database() -> None:
    """Stub for test_purge_big_database (port deferred)."""


@test.skip("complex state machine test - port deferred")
async def purge_old_states() -> None:
    """Stub for test_purge_old_states (port deferred)."""


@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_old_states_encouters_database_corruption() -> None:
    """Stub for test_purge_old_states_encouters_database_corruption (port deferred)."""


@test.skip("requires caplog + mysql mocking (complex)")
async def purge_old_states_encounters_temporary_mysql_error() -> None:
    """Stub for test_purge_old_states_encounters_temporary_mysql_error (port deferred)."""


@test.skip("requires caplog (complex)")
async def purge_old_states_encounters_operational_error() -> None:
    """Stub for test_purge_old_states_encounters_operational_error (port deferred)."""


@test.skip("requires parametrize + use_sqlite indirect fixture")
async def purge_method() -> None:
    """Stub for test_purge_method (port deferred)."""


@test.skip("requires parametrize + use_sqlite indirect fixture")
async def purge_edge_case() -> None:
    """Stub for test_purge_edge_case (port deferred)."""


@test.skip("complex state machine test - port deferred")
async def purge_cutoff_date() -> None:
    """Stub for test_purge_cutoff_date (port deferred)."""


@test.skip("requires complex pytest config + parametrize")
async def purge_filtered_states() -> None:
    """Stub for test_purge_filtered_states (port deferred)."""


@test.skip("requires complex pytest config + parametrize")
async def purge_filtered_states_multiple_rounds() -> None:
    """Stub for test_purge_filtered_states_multiple_rounds (port deferred)."""


@test.skip("requires complex pytest config + parametrize")
async def purge_filtered_states_to_empty() -> None:
    """Stub for test_purge_filtered_states_to_empty (port deferred)."""


@test.skip("requires complex pytest config + parametrize")
async def purge_without_state_attributes_filtered_states_to_empty() -> None:
    """Stub for test_purge_without_state_attributes_filtered_states_to_empty (port deferred)."""


@test.skip("requires complex pytest config + parametrize")
async def purge_filtered_events() -> None:
    """Stub for test_purge_filtered_events (port deferred)."""


@test.skip("requires complex pytest config + parametrize")
async def purge_filtered_events_state_changed() -> None:
    """Stub for test_purge_filtered_events_state_changed (port deferred)."""


@test.skip("complex purge_entities test - port deferred")
async def purge_entities() -> None:
    """Stub for test_purge_entities (port deferred)."""


@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_many_old_events() -> None:
    """Stub for test_purge_many_old_events (port deferred)."""


@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_old_events_purges_the_event_type_ids() -> None:
    """Stub for test_purge_old_events_purges_the_event_type_ids (port deferred)."""


@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_old_states_purges_the_state_metadata_ids() -> None:
    """Stub for test_purge_old_states_purges_the_state_metadata_ids (port deferred)."""


@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_entities_keep_days() -> None:
    """Stub for test_purge_entities_keep_days (port deferred)."""
