"""Tryke skip-stubs for Filter component setup tests."""

from tryke import test


@test.skip("requires recorder_mock (not in tryke shim)")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""
