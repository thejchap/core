"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires recorder_mock (not in tryke shim)")
async def exclude_attributes() -> None:
    """Stub for test_exclude_attributes (port deferred)."""
