"""Tryke skip-stubs for test_sensor.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def sensor() -> None:
    """Stub for test_sensor."""


@test.skip("zha: sibling test pending tryke port")
async def sensor_name() -> None:
    """Stub for test_sensor_name."""
