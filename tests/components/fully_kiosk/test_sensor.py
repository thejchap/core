"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors_sensors() -> None:
    """Stub for test_sensors_sensors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def url_sensor_truncating() -> None:
    """Stub for test_url_sensor_truncating."""

