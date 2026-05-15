"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def control_event() -> None:
    """Stub for test_control_event (port deferred)."""

@test.skip("snapshot test - port deferred")
async def status_event() -> None:
    """Stub for test_status_event (port deferred)."""

@test.skip("snapshot test - port deferred")
async def invalid_event_type() -> None:
    """Stub for test_invalid_event_type (port deferred)."""

@test.skip("snapshot test - port deferred")
async def ignoring_lighting4() -> None:
    """Stub for test_ignoring_lighting4 (port deferred)."""
