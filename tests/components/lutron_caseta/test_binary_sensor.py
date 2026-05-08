"""Tryke skip-stubs for lutron_caseta binary sensor tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def binary_sensor_placeholder() -> None:
    """Placeholder skipped sibling tests for test_binary_sensor.py."""
