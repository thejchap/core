"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_entry() -> None:
    """Stub for test_setup_entry (port deferred)."""

@test.skip("pending tryke port")
async def setup_entry_absent_measurement() -> None:
    """Stub for test_setup_entry_absent_measurement (port deferred)."""
