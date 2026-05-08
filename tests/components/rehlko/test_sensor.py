"""Tests for the Rehlko sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""

@test.skip("syrupy snapshot")
async def sensor_availability_device_disconnect() -> None:
    """Stub for test_sensor_availability_device_disconnect (port deferred)."""

@test.skip("syrupy snapshot")
async def sensor_availability_poll_failure() -> None:
    """Stub for test_sensor_availability_poll_failure (port deferred)."""
