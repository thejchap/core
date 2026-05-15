"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def scanner_v1() -> None:
    """Stub for test_scanner_v1 (port deferred)."""

@test.skip("pending tryke port")
async def scanner_v2() -> None:
    """Stub for test_scanner_v2 (port deferred)."""

@test.skip("pending tryke port")
async def scanner_ignores_non_ble_events() -> None:
    """Stub for test_scanner_ignores_non_ble_events (port deferred)."""

@test.skip("pending tryke port")
async def scanner_ignores_wrong_version_and_logs() -> None:
    """Stub for test_scanner_ignores_wrong_version_and_logs (port deferred)."""

@test.skip("pending tryke port")
async def scanner_warns_on_corrupt_event() -> None:
    """Stub for test_scanner_warns_on_corrupt_event (port deferred)."""
