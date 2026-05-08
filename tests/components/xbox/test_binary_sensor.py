"""Tryke skip-stubs for test_binary_sensor.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("xbox: sibling test pending tryke port")
async def binary_sensors() -> None:
    """Stub for test_binary_sensors."""


@test.skip("xbox: sibling test pending tryke port")
async def binary_sensor_deprecation_remove_disabled() -> None:
    """Stub for test_binary_sensor_deprecation_remove_disabled."""
