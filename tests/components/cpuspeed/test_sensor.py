"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sensor() -> None:
    """Stub for test_sensor."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sensor_partial_info() -> None:
    """Stub for test_sensor_partial_info."""

