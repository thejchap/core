"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires recorder_mock (not in tryke shim)")
async def time_category() -> None:
    """Stub for test_time_category (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def empty_database() -> None:
    """Stub for test_empty_database (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def invalid_user_id() -> None:
    """Stub for test_invalid_user_id (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def with_service_calls() -> None:
    """Stub for test_with_service_calls (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def multiple_entities_in_one_call() -> None:
    """Stub for test_multiple_entities_in_one_call (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def context_deduplication() -> None:
    """Stub for test_context_deduplication (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def old_events_excluded() -> None:
    """Stub for test_old_events_excluded (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def entities_limit() -> None:
    """Stub for test_entities_limit (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def different_users_separated() -> None:
    """Stub for test_different_users_separated (port deferred)."""
