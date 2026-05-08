"""Tryke skip-stubs for metoffice sensor tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def sensor_placeholder() -> None:
    """Placeholder skipped sibling tests for test_sensor.py."""
