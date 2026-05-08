"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sensors_pro() -> None:
    """Stub for test_sensors_pro."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sensors_attributes_pro() -> None:
    """Stub for test_sensors_attributes_pro."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sensors_flex() -> None:
    """Stub for test_sensors_flex."""

