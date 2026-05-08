"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def airzone_create_sensors() -> None:
    """Stub for test_airzone_create_sensors."""

