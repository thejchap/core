"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def power_sensor_detected() -> None:
    """Stub for test_power_sensor_detected."""

