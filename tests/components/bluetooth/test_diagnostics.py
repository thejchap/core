"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def diagnostics() -> None:
    """Stub for test_diagnostics (port deferred)."""

@test.skip("pending tryke port")
async def diagnostics_macos() -> None:
    """Stub for test_diagnostics_macos (port deferred)."""

@test.skip("pending tryke port")
async def diagnostics_remote_adapter() -> None:
    """Stub for test_diagnostics_remote_adapter (port deferred)."""
