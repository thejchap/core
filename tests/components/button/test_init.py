"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def button() -> None:
    """Stub for test_button (port deferred)."""

@test.skip("pending tryke port")
async def custom_integration() -> None:
    """Stub for test_custom_integration (port deferred)."""

@test.skip("pending tryke port")
async def restore_state() -> None:
    """Stub for test_restore_state (port deferred)."""

@test.skip("pending tryke port")
async def restore_state_does_not_restore_unavailable() -> None:
    """Stub for test_restore_state_does_not_restore_unavailable (port deferred)."""

@test.skip("pending tryke port")
async def name() -> None:
    """Stub for test_name (port deferred)."""
