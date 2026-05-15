"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def firmware_check_error() -> None:
    """Stub for test_firmware_check_error (port deferred)."""

@test.skip("pending tryke port")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""
