"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def triggers() -> None:
    """Stub for test_triggers (port deferred)."""

@test.skip("pending tryke port")
async def exception_bad_trigger() -> None:
    """Stub for test_exception_bad_trigger (port deferred)."""

@test.skip("pending tryke port")
async def multiple_tags_and_devices_trigger() -> None:
    """Stub for test_multiple_tags_and_devices_trigger (port deferred)."""
