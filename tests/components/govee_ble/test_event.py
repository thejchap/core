"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def motion_sensor() -> None:
    """Stub for test_motion_sensor (port deferred)."""

@test.skip("pending tryke port")
async def button() -> None:
    """Stub for test_button (port deferred)."""

@test.skip("pending tryke port")
async def vibration_sensor() -> None:
    """Stub for test_vibration_sensor (port deferred)."""
