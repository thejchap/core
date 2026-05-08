"""Test Satel Integra Binary Sensor. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def binary_sensors() -> None:
    """Stub for test_binary_sensors (port deferred)."""

@test.skip("syrupy snapshot")
async def binary_sensor_initial_state() -> None:
    """Stub for test_binary_sensor_initial_state (port deferred)."""

@test.skip("syrupy snapshot")
async def binary_sensor_callback() -> None:
    """Stub for test_binary_sensor_callback (port deferred)."""

@test.skip("syrupy snapshot")
async def binary_sensor_last_reported() -> None:
    """Stub for test_binary_sensor_last_reported (port deferred)."""

@test.skip("syrupy snapshot")
async def availability() -> None:
    """Stub for test_availability (port deferred)."""
