"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def get_domain_data() -> None:
    """Stub for test_get_domain_data (port deferred)."""

@test.skip("pending tryke port")
async def event_notifier() -> None:
    """Stub for test_event_notifier (port deferred)."""

@test.skip("pending tryke port")
async def cleanup_event_notifiers() -> None:
    """Stub for test_cleanup_event_notifiers (port deferred)."""
