"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_big_database() -> None:
    """Stub for test_purge_big_database (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_old_states() -> None:
    """Stub for test_purge_old_states (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_old_states_encouters_database_corruption() -> None:
    """Stub for test_purge_old_states_encouters_database_corruption (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_old_states_encounters_temporary_mysql_error() -> None:
    """Stub for test_purge_old_states_encounters_temporary_mysql_error (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_old_states_encounters_operational_error() -> None:
    """Stub for test_purge_old_states_encounters_operational_error (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_old_events() -> None:
    """Stub for test_purge_old_events (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_old_recorder_runs() -> None:
    """Stub for test_purge_old_recorder_runs (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_old_statistics_runs() -> None:
    """Stub for test_purge_old_statistics_runs (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_method() -> None:
    """Stub for test_purge_method (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_edge_case() -> None:
    """Stub for test_purge_edge_case (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_cutoff_date() -> None:
    """Stub for test_purge_cutoff_date (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_filtered_states() -> None:
    """Stub for test_purge_filtered_states (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_filtered_states_multiple_rounds() -> None:
    """Stub for test_purge_filtered_states_multiple_rounds (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_filtered_states_to_empty() -> None:
    """Stub for test_purge_filtered_states_to_empty (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_without_state_attributes_filtered_states_to_empty() -> None:
    """Stub for test_purge_without_state_attributes_filtered_states_to_empty (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_filtered_events() -> None:
    """Stub for test_purge_filtered_events (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_filtered_events_state_changed() -> None:
    """Stub for test_purge_filtered_events_state_changed (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
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
