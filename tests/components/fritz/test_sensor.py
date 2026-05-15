"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def sensor_setup() -> None:
    """Stub for test_sensor_setup (port deferred)."""

@test.skip("snapshot test - port deferred")
async def sensor_update_fail() -> None:
    """Stub for test_sensor_update_fail (port deferred)."""

@test.skip("snapshot test - port deferred")
async def sensor_uptime_spike() -> None:
    """Stub for test_sensor_uptime_spike (port deferred)."""

@test.skip("snapshot test - port deferred")
async def sensor_cpu_temp_not_supported() -> None:
    """Stub for test_sensor_cpu_temp_not_supported (port deferred)."""
