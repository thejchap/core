"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def v1_sensors() -> None:
    """Stub for test_v1_sensors (port deferred)."""

@test.skip("pending tryke port")
async def v2_sensors() -> None:
    """Stub for test_v2_sensors (port deferred)."""

@test.skip("pending tryke port")
async def unavailable() -> None:
    """Stub for test_unavailable (port deferred)."""

@test.skip("pending tryke port")
async def sleepy_device() -> None:
    """Stub for test_sleepy_device (port deferred)."""

@test.skip("pending tryke port")
async def sleepy_device_restore_state() -> None:
    """Stub for test_sleepy_device_restore_state (port deferred)."""
