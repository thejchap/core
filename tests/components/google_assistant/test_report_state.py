"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def report_state() -> None:
    """Stub for test_report_state (port deferred)."""

@test.skip("pending tryke port")
async def report_notifications() -> None:
    """Stub for test_report_notifications (port deferred)."""
