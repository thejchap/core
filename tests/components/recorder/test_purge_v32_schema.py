"""Tryke skip stub (requires unported fixture)."""

from tryke import test


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
async def purge_many_old_events() -> None:
    """Stub for test_purge_many_old_events (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_can_mix_legacy_and_new_format() -> None:
    """Stub for test_purge_can_mix_legacy_and_new_format (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_can_mix_legacy_and_new_format_with_detached_state() -> None:
    """Stub for test_purge_can_mix_legacy_and_new_format_with_detached_state (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def purge_entities_keep_days() -> None:
    """Stub for test_purge_entities_keep_days (port deferred)."""
