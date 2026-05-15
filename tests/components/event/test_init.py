"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def event() -> None:
    """Stub for test_event (port deferred)."""

@test.skip("pending tryke port")
async def restore_state() -> None:
    """Stub for test_restore_state (port deferred)."""

@test.skip("pending tryke port")
async def invalid_extra_restore_state() -> None:
    """Stub for test_invalid_extra_restore_state (port deferred)."""

@test.skip("pending tryke port")
async def no_extra_restore_state() -> None:
    """Stub for test_no_extra_restore_state (port deferred)."""

@test.skip("pending tryke port")
async def saving_state() -> None:
    """Stub for test_saving_state (port deferred)."""

@test.skip("pending tryke port")
async def name() -> None:
    """Stub for test_name (port deferred)."""

@test.skip("pending tryke port")
async def doorbell_missing_ring_event_type() -> None:
    """Stub for test_doorbell_missing_ring_event_type (port deferred)."""
