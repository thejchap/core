"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sensors_created() -> None:
    """Stub for test_sensors_created."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def timestamp_sensors() -> None:
    """Stub for test_timestamp_sensors."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sensor_update() -> None:
    """Stub for test_sensor_update."""

