"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def default_state() -> None:
    """Stub for test_default_state (port deferred)."""

@test.skip("pending tryke port")
async def light_service_calls() -> None:
    """Stub for test_light_service_calls (port deferred)."""

@test.skip("pending tryke port")
async def switch_service_calls() -> None:
    """Stub for test_switch_service_calls (port deferred)."""
