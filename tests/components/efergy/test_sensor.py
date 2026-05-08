"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_readings() -> None:
    """Stub for test_sensor_readings."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def multi_sensor_readings() -> None:
    """Stub for test_multi_sensor_readings."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def failed_update_and_reconnection() -> None:
    """Stub for test_failed_update_and_reconnection."""

