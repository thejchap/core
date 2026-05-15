"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def switch_state() -> None:
    """Stub for test_switch_state (port deferred)."""

@test.skip("pending tryke port")
async def switch_change_state() -> None:
    """Stub for test_switch_change_state (port deferred)."""

@test.skip("pending tryke port")
async def switch_error() -> None:
    """Stub for test_switch_error (port deferred)."""

@test.skip("pending tryke port")
async def switch_connection_error() -> None:
    """Stub for test_switch_connection_error (port deferred)."""
