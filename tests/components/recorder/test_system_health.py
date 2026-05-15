"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires recorder_mock (not in tryke shim)")
async def recorder_system_health() -> None:
    """Stub for test_recorder_system_health (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def recorder_system_health_alternate_dbms() -> None:
    """Stub for test_recorder_system_health_alternate_dbms (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def recorder_system_health_db_url_missing_host() -> None:
    """Stub for test_recorder_system_health_db_url_missing_host (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def recorder_system_health_crashed_recorder_runs_table() -> None:
    """Stub for test_recorder_system_health_crashed_recorder_runs_table (port deferred)."""
