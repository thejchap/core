"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_error() -> None:
    """Stub for test_sensor_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def register_removed() -> None:
    """Stub for test_register_removed."""

