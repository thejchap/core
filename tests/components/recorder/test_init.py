"""The tests for the Recorder component (tryke port)."""

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.db_schema import (
    EventData,
    Events,
    EventTypes,
    StateAttributes,
    States,
    StatesMeta,
)
from homeassistant.components.recorder.queries import select_event_type_ids
from homeassistant.components.recorder.util import session_scope
from homeassistant.const import MATCH_ALL
from homeassistant.core import Event, HomeAssistant, callback

from ._fixtures import recorder_mock
from .common import (
    async_recorder_block_till_done,
    async_wait_recording_done,
    db_event_data_to_native,
    db_event_to_native,
    db_state_attributes_to_native,
    db_state_to_native,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _recorder: Any = Depends(recorder_mock),
) -> int:
    """Anchor fixture for tryke Depends() resolution."""
    return 0


@test
async def saving_state(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test saving and restoring a state."""
    entity_id = "test.recorder"
    state_str = "restoring_from_db"
    attributes = {"test_attr": 5, "test_attr_10": "nice"}

    hass.states.async_set(entity_id, state_str, attributes)

    await async_wait_recording_done(hass)

    with session_scope(hass=hass, read_only=True) as session:
        db_states = []
        native_state = None
        for db_state, db_state_attributes, states_meta in (
            session.query(States, StateAttributes, StatesMeta)
            .outerjoin(
                StateAttributes, States.attributes_id == StateAttributes.attributes_id
            )
            .outerjoin(StatesMeta, States.metadata_id == StatesMeta.metadata_id)
        ):
            db_state.entity_id = states_meta.entity_id
            db_states.append(db_state)
            native_state = db_state_to_native(db_state)
            native_state.attributes = db_state_attributes_to_native(db_state_attributes)
        expect(len(db_states)).to_be(1)
        expect(db_states[0].event_id).to_be(None)

    expect(native_state.as_dict()).to_equal(hass.states.get(entity_id).as_dict())


@test
async def saving_state_with_intermixed_time_changes(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test saving states with intermixed time changes."""
    from homeassistant.components.recorder.const import KEEPALIVE_TIME
    from homeassistant.util import dt as dt_util

    from tests.common import async_fire_time_changed

    entity_id = "test.recorder"
    state_str = "restoring_from_db"
    attributes = {"test_attr": 5, "test_attr_10": "nice"}
    attributes2 = {"test_attr": 10, "test_attr_10": "mean"}

    for _ in range(KEEPALIVE_TIME + 1):
        async_fire_time_changed(hass, dt_util.utcnow())
    hass.states.async_set(entity_id, state_str, attributes)
    for _ in range(KEEPALIVE_TIME + 1):
        async_fire_time_changed(hass, dt_util.utcnow())
    hass.states.async_set(entity_id, state_str, attributes2)

    await async_wait_recording_done(hass)

    with session_scope(hass=hass, read_only=True) as session:
        db_states = list(session.query(States))
        expect(len(db_states)).to_be(2)
        expect(db_states[0].event_id).to_be(None)


@test
async def saving_event(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test saving and restoring an event."""
    event_type = "EVENT_TEST"
    event_data = {"test_attr": 5, "test_attr_10": "nice"}

    events: list[Event] = []

    @callback
    def event_listener(event: Event) -> None:
        if event.event_type == event_type:
            events.append(event)

    hass.bus.async_listen(MATCH_ALL, event_listener)
    hass.bus.async_fire(event_type, event_data)

    await async_wait_recording_done(hass)

    expect(len(events)).to_be(1)
    event = events[0]

    await async_recorder_block_till_done(hass)
    db_events: list[Event] = []

    with session_scope(hass=hass, read_only=True) as session:
        for select_event, edata, etypes in (
            session.query(Events, EventData, EventTypes)
            .filter(Events.event_type_id.in_(select_event_type_ids((event_type,))))
            .outerjoin(EventTypes, Events.event_type_id == EventTypes.event_type_id)
            .outerjoin(EventData, Events.data_id == EventData.data_id)
        ):
            native_event = db_event_to_native(select_event)
            native_event.data = db_event_data_to_native(edata)
            native_event.event_type = etypes.event_type
            db_events.append(native_event)

    db_event = db_events[0]

    expect(event.event_type).to_equal(db_event.event_type)
    expect(event.data).to_equal(db_event.data)
    expect(event.origin).to_equal(db_event.origin)
    expect(event.time_fired.replace(microsecond=0)).to_equal(
        db_event.time_fired.replace(microsecond=0)
    )


@test
async def has_services(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the existence of the recorder services."""
    from homeassistant.components.recorder import DOMAIN
    from homeassistant.components.recorder.services import (
        SERVICE_DISABLE,
        SERVICE_ENABLE,
        SERVICE_PURGE,
        SERVICE_PURGE_ENTITIES,
    )

    expect(hass.services.has_service(DOMAIN, SERVICE_DISABLE)).to_be(True)
    expect(hass.services.has_service(DOMAIN, SERVICE_ENABLE)).to_be(True)
    expect(hass.services.has_service(DOMAIN, SERVICE_PURGE)).to_be(True)
    expect(hass.services.has_service(DOMAIN, SERVICE_PURGE_ENTITIES)).to_be(True)


@test
async def in_memory_database(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test connecting to an in-memory recorder is possible."""
    instance = get_instance(hass)
    expect(instance is not None).to_be(True)


# Stubs for tests that need fixtures not yet ported (async_setup_recorder_instance,
# async_test_recorder, instrument_migration, etc.).

@test.skip("requires async_setup_recorder_instance (not in tryke shim)")
async def shutdown_before_startup_finishes() -> None:
    """Stub for test_shutdown_before_startup_finishes (port deferred)."""


@test.skip("requires async_setup_recorder_instance (not in tryke shim)")
async def canceled_before_startup_finishes() -> None:
    """Stub for test_canceled_before_startup_finishes (port deferred)."""


@test.skip("requires async_setup_recorder_instance (not in tryke shim)")
async def shutdown_closes_connections() -> None:
    """Stub for test_shutdown_closes_connections (port deferred)."""


@test.skip("requires async_setup_recorder_instance (not in tryke shim)")
async def state_gets_saved_when_set_before_start_event() -> None:
    """Stub for test_state_gets_saved_when_set_before_start_event (port deferred)."""


@test.skip("requires recorder_dialect_name fixture (not in tryke shim)")
async def saving_state_with_nul() -> None:
    """Stub for test_saving_state_with_nul (port deferred)."""


@test.skip("requires async_setup_recorder_instance (not in tryke shim)")
async def saving_many_states() -> None:
    """Stub for test_saving_many_states (port deferred)."""


@test.skip("requires caplog fixture (not in tryke shim)")
async def saving_state_with_exception() -> None:
    """Stub for test_saving_state_with_exception (port deferred)."""


@test.skip("requires caplog fixture (not in tryke shim)")
async def saving_state_with_sqlalchemy_exception() -> None:
    """Stub for test_saving_state_with_sqlalchemy_exception (port deferred)."""


@test.skip("requires async_setup_recorder_instance + caplog (not in tryke shim)")
async def force_shutdown_with_queue_of_writes_that_generate_exceptions() -> None:
    """Stub for test_force_shutdown_with_queue_of_writes_that_generate_exceptions (port deferred)."""


@test.skip("requires async_setup_recorder_instance (not in tryke shim)")
async def saving_state_with_commit_interval_zero() -> None:
    """Stub for test_saving_state_with_commit_interval_zero (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def setup_without_migration() -> None:
    """Stub for test_setup_without_migration (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def saving_state_include_domains() -> None:
    """Stub for test_saving_state_include_domains (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def saving_state_include_domains_globs() -> None:
    """Stub for test_saving_state_include_domains_globs (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def saving_state_incl_entities() -> None:
    """Stub for test_saving_state_incl_entities (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def saving_event_exclude_event_type() -> None:
    """Stub for test_saving_event_exclude_event_type (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def saving_state_exclude_domains() -> None:
    """Stub for test_saving_state_exclude_domains (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def saving_state_exclude_domains_globs() -> None:
    """Stub for test_saving_state_exclude_domains_globs (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def saving_state_exclude_entities() -> None:
    """Stub for test_saving_state_exclude_entities (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def saving_state_exclude_domain_include_entity() -> None:
    """Stub for test_saving_state_exclude_domain_include_entity (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def saving_state_exclude_domain_glob_include_entity() -> None:
    """Stub for test_saving_state_exclude_domain_glob_include_entity (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def saving_state_include_domain_exclude_entity() -> None:
    """Stub for test_saving_state_include_domain_exclude_entity (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def saving_state_include_domain_glob_exclude_entity() -> None:
    """Stub for test_saving_state_include_domain_glob_exclude_entity (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def saving_state_and_removing_entity() -> None:
    """Stub for test_saving_state_and_removing_entity (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def saving_state_with_oversized_attributes() -> None:
    """Stub for test_saving_state_with_oversized_attributes (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def saving_event_with_oversized_data() -> None:
    """Stub for test_saving_event_with_oversized_data (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def saving_event_invalid_context_ulid() -> None:
    """Stub for test_saving_event_invalid_context_ulid (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def recorder_setup_failure() -> None:
    """Stub for test_recorder_setup_failure (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def recorder_validate_schema_failure() -> None:
    """Stub for test_recorder_validate_schema_failure (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def recorder_setup_failure_without_event_listener() -> None:
    """Stub for test_recorder_setup_failure_without_event_listener (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def defaults_set() -> None:
    """Stub for test_defaults_set (port deferred)."""


@test.skip("requires freezer fixture (not in tryke shim)")
async def auto_purge() -> None:
    """Stub for test_auto_purge (port deferred)."""


@test.skip("requires freezer fixture (not in tryke shim)")
async def auto_purge_auto_repack_on_second_sunday() -> None:
    """Stub for test_auto_purge_auto_repack_on_second_sunday (port deferred)."""


@test.skip("requires freezer fixture (not in tryke shim)")
async def auto_purge_auto_repack_disabled_on_second_sunday() -> None:
    """Stub for test_auto_purge_auto_repack_disabled_on_second_sunday (port deferred)."""


@test.skip("requires freezer fixture (not in tryke shim)")
async def auto_purge_no_auto_repack_on_not_second_sunday() -> None:
    """Stub for test_auto_purge_no_auto_repack_on_not_second_sunday (port deferred)."""


@test.skip("requires freezer fixture (not in tryke shim)")
async def auto_purge_disabled() -> None:
    """Stub for test_auto_purge_disabled (port deferred)."""


@test.skip("requires freezer fixture (not in tryke shim)")
async def auto_statistics() -> None:
    """Stub for test_auto_statistics (port deferred)."""


@test.skip("requires freezer fixture (not in tryke shim)")
async def statistics_runs_initiated() -> None:
    """Stub for test_statistics_runs_initiated (port deferred)."""


@test.skip("requires freezer fixture (not in tryke shim)")
async def compile_missing_statistics() -> None:
    """Stub for test_compile_missing_statistics (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def saving_sets_old_state() -> None:
    """Stub for test_saving_sets_old_state (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def saving_state_with_serializable_data() -> None:
    """Stub for test_saving_state_with_serializable_data (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def service_disable_events_not_recording() -> None:
    """Stub for test_service_disable_events_not_recording (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def service_disable_states_not_recording() -> None:
    """Stub for test_service_disable_states_not_recording (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def service_disable_run_information_recorded() -> None:
    """Stub for test_service_disable_run_information_recorded (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def database_corruption_while_running() -> None:
    """Stub for test_database_corruption_while_running (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def entity_id_filter() -> None:
    """Stub for test_entity_id_filter (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def database_lock_and_unlock() -> None:
    """Stub for test_database_lock_and_unlock (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def database_lock_and_overflow() -> None:
    """Stub for test_database_lock_and_overflow (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def database_lock_and_overflow_checks_available_memory() -> None:
    """Stub for test_database_lock_and_overflow_checks_available_memory (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def database_lock_timeout() -> None:
    """Stub for test_database_lock_timeout (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def database_lock_without_instance() -> None:
    """Stub for test_database_lock_without_instance (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def database_connection_keep_alive() -> None:
    """Stub for test_database_connection_keep_alive (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def database_connection_keep_alive_disabled_on_sqlite() -> None:
    """Stub for test_database_connection_keep_alive_disabled_on_sqlite (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def deduplication_event_data_inside_commit_interval() -> None:
    """Stub for test_deduplication_event_data_inside_commit_interval (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def deduplication_state_attributes_inside_commit_interval() -> None:
    """Stub for test_deduplication_state_attributes_inside_commit_interval (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def async_block_till_done() -> None:
    """Stub for test_async_block_till_done (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def disable_echo() -> None:
    """Stub for test_disable_echo (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def mysql_missing_utf8mb4() -> None:
    """Stub for test_mysql_missing_utf8mb4 (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def connect_args_priority() -> None:
    """Stub for test_connect_args_priority (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def excluding_attributes_by_integration() -> None:
    """Stub for test_excluding_attributes_by_integration (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def excluding_all_attributes_by_integration() -> None:
    """Stub for test_excluding_all_attributes_by_integration (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def lru_increases_with_many_entities() -> None:
    """Stub for test_lru_increases_with_many_entities (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def clean_shutdown_when_recorder_thread_raises_during_initialize_database() -> None:
    """Stub for test_clean_shutdown_when_recorder_thread_raises_during_initialize_database (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def clean_shutdown_when_recorder_thread_raises_during_validate_db_schema() -> None:
    """Stub for test_clean_shutdown_when_recorder_thread_raises_during_validate_db_schema (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def clean_shutdown_when_schema_migration_fails() -> None:
    """Stub for test_clean_shutdown_when_schema_migration_fails (port deferred)."""


@test.skip("requires caplog (not in tryke shim)")
async def setup_fails_after_downgrade() -> None:
    """Stub for test_setup_fails_after_downgrade (port deferred)."""


@test.skip("requires async_setup_recorder_instance (not in tryke shim)")
async def events_are_recorded_until_final_write() -> None:
    """Stub for test_events_are_recorded_until_final_write (port deferred)."""


@test.skip("requires async_setup_recorder_instance (not in tryke shim)")
async def commit_before_commits_pending_writes() -> None:
    """Stub for test_commit_before_commits_pending_writes (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def all_tables_use_default_table_args() -> None:
    """Stub for test_all_tables_use_default_table_args (port deferred)."""


@test.skip("requires recorder_mock variants (not in tryke shim)")
async def empty_entity_id() -> None:
    """Stub for test_empty_entity_id (port deferred)."""


@test.skip("requires async_setup_recorder_instance (not in tryke shim)")
async def setting_up_recorder_fails_entity_registry_listener() -> None:
    """Stub for test_setting_up_recorder_fails_entity_registry_listener (port deferred)."""
