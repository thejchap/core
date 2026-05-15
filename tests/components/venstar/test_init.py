"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_entry() -> None:
    """Stub for test_setup_entry (port deferred)."""

@test.skip("pending tryke port")
async def setup_entry_exception() -> None:
    """Stub for test_setup_entry_exception (port deferred)."""

@test.skip("pending tryke port")
async def silent_failure_triggers_retry() -> None:
    """Stub for test_silent_failure_triggers_retry (port deferred)."""
