"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def v1_binary_sensors() -> None:
    """Stub for test_v1_binary_sensors (port deferred)."""

@test.skip("pending tryke port")
async def v2_binary_sensors() -> None:
    """Stub for test_v2_binary_sensors (port deferred)."""

@test.skip("pending tryke port")
async def unavailable() -> None:
    """Stub for test_unavailable (port deferred)."""

@test.skip("pending tryke port")
async def sleepy_device() -> None:
    """Stub for test_sleepy_device (port deferred)."""

@test.skip("pending tryke port")
async def sleepy_device_restores_state() -> None:
    """Stub for test_sleepy_device_restores_state (port deferred)."""
