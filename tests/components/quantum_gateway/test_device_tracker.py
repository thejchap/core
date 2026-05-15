"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def get_scanner() -> None:
    """Stub for test_get_scanner (port deferred)."""

@test.skip("pending tryke port")
async def get_scanner_error() -> None:
    """Stub for test_get_scanner_error (port deferred)."""

@test.skip("pending tryke port")
async def scan_devices_error() -> None:
    """Stub for test_scan_devices_error (port deferred)."""
