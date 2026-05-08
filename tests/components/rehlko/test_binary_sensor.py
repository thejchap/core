"""Tests for the Rehlko binary sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""

@test.skip("syrupy snapshot")
async def binary_sensor_states() -> None:
    """Stub for test_binary_sensor_states (port deferred)."""

@test.skip("syrupy snapshot")
async def loadshed_binary_sensor_states() -> None:
    """Stub for test_loadshed_binary_sensor_states (port deferred)."""

@test.skip("syrupy snapshot")
async def binary_sensor_connectivity_availability() -> None:
    """Stub for test_binary_sensor_connectivity_availability (port deferred)."""
