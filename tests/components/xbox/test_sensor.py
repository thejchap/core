"""Tryke skip-stubs for test_sensor.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("xbox: sibling test pending tryke port")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("xbox: sibling test pending tryke port")
async def sensor_deprecation_remove_entity() -> None:
    """Stub for test_sensor_deprecation_remove_entity."""
