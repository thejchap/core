"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sensors_unknown() -> None:
    """Stub for test_sensors_unknown."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sensors_update_failed() -> None:
    """Stub for test_sensors_update_failed."""

