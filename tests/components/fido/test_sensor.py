"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def fido_sensor() -> None:
    """Stub for test_fido_sensor (port deferred)."""

@test.skip("pending tryke port")
async def error() -> None:
    """Stub for test_error (port deferred)."""
