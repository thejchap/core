"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def light_state() -> None:
    """Stub for test_light_state (port deferred)."""

@test.skip("pending tryke port")
async def change_state() -> None:
    """Stub for test_change_state (port deferred)."""

@test.skip("pending tryke port")
async def sleep_timer_services() -> None:
    """Stub for test_sleep_timer_services (port deferred)."""

@test.skip("pending tryke port")
async def light_error() -> None:
    """Stub for test_light_error (port deferred)."""

@test.skip("pending tryke port")
async def light_connection_error() -> None:
    """Stub for test_light_connection_error (port deferred)."""
